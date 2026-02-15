# Tool Discovery & Search - Implementation Specification

META::
  type: feature
  component: tool-discovery-search
  dependencies: foundation,tool-inventory
  tech_stack: ASP.NET Core 8, React 18, PostgreSQL 16
  estimated_effort_hours: 30
::META

---

## IMPLEMENTATION_ORDER

STEP_1: Database schema updates and search indexes
STEP_2: Search domain entities and DTOs
STEP_3: Search repository interface and implementation
STEP_4: Search service layer with geospatial logic
STEP_5: Search API controller
STEP_6: Search request/response DTOs and validation
STEP_7: Frontend search API client
STEP_8: Search components and UI
STEP_9: Unit tests for search logic
STEP_10: Integration tests for search endpoints

---

## DATABASE_SCHEMA

### TABLE::Tools_SearchIndexes
```sql
-- Add search indexes to existing Tools table
CREATE INDEX "IX_Tools_SearchVector" ON "Tools" 
USING GIN(to_tsvector('english', "Title" || ' ' || "Description" || ' ' || "Brand" || ' ' || "Model"));

CREATE INDEX "IX_Tools_Category_Available" ON "Tools"("Category", "IsAvailable", "IsDeleted");

CREATE INDEX "IX_Tools_Location" ON "Tools"("LocationLatitude", "LocationLongitude") 
WHERE "LocationLatitude" IS NOT NULL AND "LocationLongitude" IS NOT NULL;

CREATE INDEX "IX_Tools_Condition" ON "Tools"("Condition");
```
::TABLE

### TABLE::ToolSearchSynonyms
```sql
CREATE TABLE "ToolSearchSynonyms" (
    "Id" serial PRIMARY KEY,
    "Term" varchar(100) NOT NULL,
    "Synonym" varchar(100) NOT NULL,
    "CreatedAt" timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX "IX_ToolSearchSynonyms_Term" ON "ToolSearchSynonyms"("Term");

-- Insert initial synonyms
INSERT INTO "ToolSearchSynonyms" ("Term", "Synonym") VALUES
('drill', 'driver'),
('wrench', 'spanner'),
('mower', 'lawnmower'),
('saw', 'circular saw'),
('grinder', 'angle grinder'),
('blower', 'leaf blower'),
('washer', 'pressure washer'),
('ladder', 'step ladder'),
('sander', 'belt sander'),
('trimmer', 'hedge trimmer');
```
::TABLE

### MIGRATION::20260216_AddToolSearchIndexes
```csharp
public partial class AddToolSearchIndexes : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        // COPY THIS EXACTLY
        migrationBuilder.Sql(@"
            CREATE INDEX ""IX_Tools_SearchVector"" ON ""Tools"" 
            USING GIN(to_tsvector('english', ""Title"" || ' ' || ""Description"" || ' ' || ""Brand"" || ' ' || ""Model""));
        ");
        
        migrationBuilder.Sql(@"
            CREATE INDEX ""IX_Tools_Category_Available"" ON ""Tools""(""Category"", ""IsAvailable"", ""IsDeleted"");
        ");
        
        migrationBuilder.Sql(@"
            CREATE INDEX ""IX_Tools_Location"" ON ""Tools""(""LocationLatitude"", ""LocationLongitude"") 
            WHERE ""LocationLatitude"" IS NOT NULL AND ""LocationLongitude"" IS NOT NULL;
        ");
        
        migrationBuilder.Sql(@"
            CREATE INDEX ""IX_Tools_Condition"" ON ""Tools""(""Condition"");
        ");

        migrationBuilder.CreateTable(
            name: "ToolSearchSynonyms",
            columns: table => new
            {
                Id = table.Column<int>(type: "serial", nullable: false)
                    .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.SerialColumn),
                Term = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                Synonym = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()")
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_ToolSearchSynonyms", x => x.Id);
            });

        migrationBuilder.CreateIndex(
            name: "IX_ToolSearchSynonyms_Term",
            table: "ToolSearchSynonyms",
            column: "Term");

        // Insert initial synonyms
        migrationBuilder.Sql(@"
            INSERT INTO ""ToolSearchSynonyms"" (""Term"", ""Synonym"") VALUES
            ('drill', 'driver'),
            ('wrench', 'spanner'),
            ('mower', 'lawnmower'),
            ('saw', 'circular saw'),
            ('grinder', 'angle grinder'),
            ('blower', 'leaf blower'),
            ('washer', 'pressure washer'),
            ('ladder', 'step ladder'),
            ('sander', 'belt sander'),
            ('trimmer', 'hedge trimmer');
        ");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "ToolSearchSynonyms");
        migrationBuilder.DropIndex(name: "IX_Tools_SearchVector", table: "Tools");
        migrationBuilder.DropIndex(name: "IX_Tools_Category_Available", table: "Tools");
        migrationBuilder.DropIndex(name: "IX_Tools_Location", table: "Tools");
        migrationBuilder.DropIndex(name: "IX_Tools_Condition", table: "Tools");
    }
}
```
::MIGRATION

---

## DOMAIN_ENTITIES

### ENTITY::ToolSearchSynonym
FILE: src/Domain/Entities/ToolSearchSynonym.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
using System;

namespace YourApp.Domain.Entities;

public class ToolSearchSynonym
{
    public int Id { get; init; }
    public string Term { get; init; } = null!;
    public string Synonym { get; init; } = null!;
    public DateTime CreatedAt { get; init; }
}
```
::ENTITY

### ENTITY::SearchFilters
FILE: src/Domain/ValueObjects/SearchFilters.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
using System;
using System.Collections.Generic;
using YourApp.Domain.Enums;

namespace YourApp.Domain.ValueObjects;

public record SearchFilters
{
    public double? UserLatitude { get; init; }
    public double? UserLongitude { get; init; }
    public double MaxDistanceMiles { get; init; } = 2.0;
    public bool AvailableOnly { get; init; } = true;
    public List<ToolCondition> Conditions { get; init; } = new();
    public List<ToolCategory> Categories { get; init; } = new();
}
```
::ENTITY

---

## EF_CORE_CONFIGURATIONS

### CONFIG::ToolSearchSynonymConfiguration
FILE: src/Infrastructure/Data/Configurations/ToolSearchSynonymConfiguration.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using YourApp.Domain.Entities;

namespace YourApp.Infrastructure.Data.Configurations;

public class ToolSearchSynonymConfiguration : IEntityTypeConfiguration<ToolSearchSynonym>
{
    public void Configure(EntityTypeBuilder<ToolSearchSynonym> builder)
    {
        builder.ToTable("ToolSearchSynonyms");
        
        builder.HasKey(x => x.Id);
        
        builder.Property(x => x.Term)
            .IsRequired()
            .HasMaxLength(100);
        
        builder.Property(x => x.Synonym)
            .IsRequired()
            .HasMaxLength(100);
        
        builder.Property(x => x.CreatedAt)
            .IsRequired()
            .HasDefaultValueSql("now()");
        
        builder.HasIndex(x => x.Term);
    }
}
```
::CONFIG

---

## API_ENDPOINTS

### ENDPOINT::GET_/api/v1/tools/search
REQUEST:
```json
GET /api/v1/tools/search?query=drill&maxDistance=2&availableOnly=true&conditions=LikeNew,Good&categories=PowerTools&page=1&pageSize=20
```

RESPONSE_200:
```json
{
  "tools": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Cordless Power Drill",
      "description": "Milwaukee 18V cordless drill with two batteries",
      "brand": "Milwaukee",
      "model": "M18",
      "category": "PowerTools",
      "condition": "Good",
      "estimatedValue": 120.00,
      "photos": [
        {
          "id": "photo-uuid-1",
          "photoUrl": "https://storage.example.com/tools/drill-1.jpg",
          "photoOrder": 1
        }
      ],
      "owner": {
        "id": "owner-uuid",
        "name": "John Smith",
        "photoUrl": "https://storage.example.com/users/john.jpg"
      },
      "isAvailable": true,
      "distanceMiles": 1.3,
      "approximateLocation": "Downtown Seattle"
    }
  ],
  "totalCount": 47,
  "hasMore": true,
  "searchQuery": "drill",
  "appliedFilters": {
    "maxDistanceMiles": 2.0,
    "availableOnly": true,
    "conditions": ["LikeNew", "Good"],
    "categories": ["PowerTools"]
  }
}
```

RESPONSE_400:
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "Invalid search parameters",
  "status": 400,
  "errors": {
    "MaxDistance": ["Maximum distance must be between 0.5 and 5 miles"]
  }
}
```

CONTROLLER:
FILE: src/API/Controllers/ToolsController.cs
```csharp
// COPY THIS EXACTLY - ADD THIS TO EXISTING ToolsController
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using YourApp.Application.DTOs;
using YourApp.Application.Services;

namespace YourApp.API.Controllers;

public partial class ToolsController : ControllerBase
{
    private readonly IToolSearchService _searchService;

    // ADD this constructor parameter to existing controller
    // public ToolsController(IToolService toolService, IToolSearchService searchService)

    [HttpGet("search")]
    [Authorize]
    [ProducesResponseType(typeof(ToolSearchResultDto), 200)]
    [ProducesResponseType(typeof(ProblemDetails), 400)]
    public async Task<ActionResult<ToolSearchResultDto>> Search([FromQuery] ToolSearchRequest request)
    {
        var currentUserId = Guid.Parse(User.FindFirst("sub")?.Value ?? 
            throw new UnauthorizedAccessException("User ID not found in token"));
        
        var result = await _searchService.SearchToolsAsync(request, currentUserId);
        return Ok(result);
    }

    [HttpGet("categories")]
    [ProducesResponseType(typeof(List<string>), 200)]
    public ActionResult<List<string>> GetCategories()
    {
        var categories = Enum.GetNames<ToolCategory>().ToList();
        return Ok(categories);
    }

    [HttpGet("conditions")]
    [ProducesResponseType(typeof(List<string>), 200)]
    public ActionResult<List<string>> GetConditions()
    {
        var conditions = Enum.GetNames<ToolCondition>().ToList();
        return Ok(conditions);
    }
}
```
::ENDPOINT

---

## SERVICE_LAYER

### INTERFACE::IToolSearchService
FILE: src/Application/Services/IToolSearchService.cs
```csharp
// COPY THIS EXACTLY
using YourApp.Application.DTOs;

namespace YourApp.Application.Services;

public interface IToolSearchService
{
    Task<ToolSearchResultDto> SearchToolsAsync(ToolSearchRequest request, Guid currentUserId);
    Task<List<string>> GetPopularSearchTermsAsync();
    Task<List<ToolSuggestionDto>> GetSearchSuggestionsAsync(string partialQuery);
}
```
::INTERFACE

### IMPLEMENTATION::ToolSearchService
FILE: src/Infrastructure/Services/ToolSearchService.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.EntityFrameworkCore;
using YourApp.Application.DTOs;
using YourApp.Application.Services;
using YourApp.Domain.Entities;
using YourApp.Domain.Enums;
using YourApp.Domain.ValueObjects;
using YourApp.Infrastructure.Data;

namespace YourApp.Infrastructure.Services;

public class ToolSearchService : IToolSearchService
{
    private readonly ApplicationDbContext _context;
    private const int MaxResultsLimit = 50;
    private const double DistanceMultiplier = 1.3; // Approximate driving distance from straight-line

    public ToolSearchService(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<ToolSearchResultDto> SearchToolsAsync(ToolSearchRequest request, Guid currentUserId)
    {
        // GET USER LOCATION: Retrieve user's saved location for distance calculations
        var user = await _context.Users
            .AsNoTracking()
            .FirstOrDefaultAsync(u => u.Id == currentUserId);

        if (user?.LocationLatitude == null || user.LocationLongitude == null)
        {
            throw new InvalidOperationException("User location required for search. Please update your location in settings.");
        }

        // BUILD FILTERS: Convert request to domain filters
        var filters = new SearchFilters
        {
            UserLatitude = user.LocationLatitude,
            UserLongitude = user.LocationLongitude,
            MaxDistanceMiles = request.MaxDistanceMiles,
            AvailableOnly = request.AvailableOnly,
            Conditions = request.Conditions?.Select(c => Enum.Parse<ToolCondition>(c)).ToList() ?? new List<ToolCondition>(),
            Categories = request.Categories?.Select(c => Enum.Parse<ToolCategory>(c)).ToList() ?? new List<ToolCategory>()
        };

        // EXPAND QUERY: Add synonyms to search terms
        var expandedQuery = await ExpandSearchQueryAsync(request.Query ?? string.Empty);

        // EXECUTE SEARCH: Build and run PostgreSQL query
        var query = BuildSearchQuery(expandedQuery, filters, currentUserId);
        
        var tools = await query
            .Take(MaxResultsLimit)
            .ToListAsync();

        // CALCULATE DISTANCES: Add distance information to results
        var toolDtos = tools.Select(tool => new ToolSearchItemDto
        {
            Id = tool.Id,
            Title = tool.Title,
            Description = tool.Description,
            Brand = tool.Brand,
            Model = tool.Model,
            Category = tool.Category.ToString(),
            Condition = tool.Condition.ToString(),
            EstimatedValue = tool.EstimatedValue,
            Photos = tool.Photos
                .Where(p => !p.IsDeleted)
                .OrderBy(p => p.PhotoOrder)
                .Select(p => new ToolPhotoDto
                {
                    Id = p.Id,
                    PhotoUrl = p.PhotoUrl,
                    PhotoOrder = p.PhotoOrder
                }).ToList(),
            Owner = new ToolOwnerDto
            {
                Id = tool.Owner.Id,
                Name = tool.Owner.Name,
                PhotoUrl = tool.Owner.PhotoUrl
            },
            IsAvailable = tool.IsAvailable,
            DistanceMiles = CalculateDistance(
                user.LocationLatitude.Value,
                user.LocationLongitude.Value,
                tool.LocationLatitude ?? 0,
                tool.LocationLongitude ?? 0
            ),
            ApproximateLocation = GetApproximateLocation(tool.LocationLatitude, tool.LocationLongitude)
        }).ToList();

        // COUNT TOTAL: For pagination info (limited to MaxResultsLimit)
        var totalCount = Math.Min(tools.Count, MaxResultsLimit);

        return new ToolSearchResultDto
        {
            Tools = toolDtos,
            TotalCount = totalCount,
            HasMore = tools.Count >= MaxResultsLimit,
            SearchQuery = request.Query,
            AppliedFilters = new AppliedFiltersDto
            {
                MaxDistanceMiles = filters.MaxDistanceMiles,
                AvailableOnly = filters.AvailableOnly,
                Conditions = filters.Conditions.Select(c => c.ToString()).ToList(),
                Categories = filters.Categories.Select(c => c.ToString()).ToList()
            }
        };
    }

    private IQueryable<Tool> BuildSearchQuery(string expandedQuery, SearchFilters filters, Guid currentUserId)
    {
        var query = _context.Tools
            .AsNoTracking()
            .Include(t => t.Photos.Where(p => !p.IsDeleted))
            .Include(t => t.Owner)
            .Where(t => !t.IsDeleted && t.OwnerId != currentUserId); // Exclude user's own tools

        // AVAILABILITY FILTER: Only show available tools if requested
        if (filters.AvailableOnly)
        {
            query = query.Where(t => t.IsAvailable);
        }

        // CONDITION FILTER: Filter by tool conditions
        if (filters.Conditions.Any())
        {
            query = query.Where(t => filters.Conditions.Contains(t.Condition));
        }

        // CATEGORY FILTER: Filter by tool categories
        if (filters.Categories.Any())
        {
            query = query.Where(t => filters.Categories.Contains(t.Category));
        }

        // TEXT SEARCH: Use PostgreSQL full-text search
        if (!string.IsNullOrWhiteSpace(expandedQuery))
        {
            query = query.Where(t => 
                EF.Functions.ToTsVector("english", t.Title + " " + t.Description + " " + t.Brand + " " + t.Model)
                .Matches(EF.Functions.PhraseToTsQuery("english", expandedQuery)));
        }

        // LOCATION FILTER: Use Haversine formula for distance
        if (filters.UserLatitude.HasValue && filters.UserLongitude.HasValue)
        {
            var userLat = filters.UserLatitude.Value;
            var userLng = filters.UserLongitude.Value;
            var maxDistanceKm = filters.MaxDistanceMiles * 1.60934; // Convert miles to km

            query = query.Where(t => 
                t.LocationLatitude != null && 
                t.LocationLongitude != null &&
                // Haversine formula in SQL
                (6371 * Math.Acos(
                    Math.Cos(userLat * Math.PI / 180) * 
                    Math.Cos(t.LocationLatitude.Value * Math.PI / 180) * 
                    Math.Cos((t.LocationLongitude.Value - userLng) * Math.PI / 180) + 
                    Math.Sin(userLat * Math.PI / 180) * 
                    Math.Sin(t.LocationLatitude.Value * Math.PI / 180)
                )) <= maxDistanceKm);

            // ORDER BY DISTANCE: Closest tools first
            query = query.OrderBy(t => 
                6371 * Math.Acos(
                    Math.Cos(userLat * Math.PI / 180) * 
                    Math.Cos(t.LocationLatitude.Value * Math.PI / 180) * 
                    Math.Cos((t.LocationLongitude.Value - userLng) * Math.PI / 180) + 
                    Math.Sin(userLat * Math.PI / 180) * 
                    Math.Sin(t.LocationLatitude.Value * Math.PI / 180)
                ));
        }
        else
        {
            // ORDER BY RECENT: If no location, show recently added tools first
            query = query.OrderByDescending(t => t.CreatedAt);
        }

        return query;
    }

    private async Task<string> ExpandSearchQueryAsync(string originalQuery)
    {
        if (string.IsNullOrWhiteSpace(originalQuery))
            return string.Empty;

        // GET SYNONYMS: Find all synonyms for query terms
        var queryTerms = originalQuery.ToLower().Split(' ', StringSplitOptions.RemoveEmptyEntries);
        var synonyms = await _context.ToolSearchSynonyms
            .Where(s => queryTerms.Contains(s.Term.ToLower()))
            .Select(s => s.Synonym)
            .ToListAsync();

        // COMBINE: Original query + synonyms
        var allTerms = queryTerms.Concat(synonyms).Distinct();
        return string.Join(" | ", allTerms); // PostgreSQL OR syntax
    }

    private double CalculateDistance(double lat1, double lng1, double lat2, double lng2)
    {
        // HAVERSINE FORMULA: Calculate straight-line distance
        const double R = 3959; // Earth's radius in miles

        var dLat = (lat2 - lat1) * Math.PI / 180;
        var dLng = (lng2 - lng1) * Math.PI / 180;

        var a = Math.Sin(dLat / 2) * Math.Sin(dLat / 2) +
                Math.Cos(lat1 * Math.PI / 180) * Math.Cos(lat2 * Math.PI / 180) *
                Math.Sin(dLng / 2) * Math.Sin(dLng / 2);

        var c = 2 * Math.Atan2(Math.Sqrt(a), Math.Sqrt(1 - a));
        var distance = R * c;

        // APPLY MULTIPLIER: Approximate driving distance
        return Math.Round(distance * DistanceMultiplier, 1);
    }

    private string GetApproximateLocation(double? latitude, double? longitude)
    {
        if (!latitude.HasValue || !longitude.HasValue)
            return "Location not available";

        // PRIVACY: Return neighborhood-level description
        // In production, use reverse geocoding service to get neighborhood name
        // For MVP, return generic area description
        return "Local area";
    }

    public async Task<List<string>> GetPopularSearchTermsAsync()
    {
        // POPULAR TERMS: Return common tool categories for search suggestions
        // In production, track actual search terms and return most popular
        return new List<string>
        {
            "drill", "saw", "hammer", "wrench", "screwdriver",
            "ladder", "mower", "trimmer", "blower", "washer"
        };
    }

    public async Task<List<ToolSuggestionDto>> GetSearchSuggestionsAsync(string partialQuery)
    {
        if (string.IsNullOrWhiteSpace(partialQuery) || partialQuery.Length < 2)
            return new List<ToolSuggestionDto>();

        // AUTOCOMPLETE: Find tools matching partial query
        var suggestions = await _context.Tools
            .Where(t => !t.IsDeleted && t.IsAvailable)
            .Where(t => 
                t.Title.ToLower().Contains(partialQuery.ToLower()) ||
                t.Brand.ToLower().Contains(partialQuery.ToLower()) ||
                t.Category.ToString().ToLower().Contains(partialQuery.ToLower()))
            .GroupBy(t => t.Title.ToLower())
            .Select(g => new ToolSuggestionDto
            {
                Title = g.First().Title,
                Category = g.First().Category.ToString(),
                Count = g.Count()
            })
            .OrderByDescending(s => s.Count)
            .Take(5)
            .ToListAsync();

        return suggestions;
    }
}
```
::IMPLEMENTATION

---

## DTOS

### DTO::ToolSearchRequest
FILE: src/Application/DTOs/ToolSearchRequest.cs
```csharp
// COPY THIS EXACTLY
using System.ComponentModel.DataAnnotations;

namespace YourApp.Application.DTOs;

public record ToolSearchRequest
{
    public string? Query { get; init; }
    
    [Range(0.5, 5.0)]
    public double MaxDistanceMiles { get; init; } = 2.0;
    
    public bool AvailableOnly { get; init; } = true;
    
    public List<string>? Conditions { get; init; }
    
    public List<string>? Categories { get; init; }
    
    [Range(1, 50)]
    public int PageSize { get; init; } = 20;
    
    [Range(1, int.MaxValue)]
    public int Page { get; init; } = 1;
}
```
::DTO

### DTO::ToolSearchResultDto
FILE: src/Application/DTOs/ToolSearchResultDto.cs
```csharp
// COPY THIS EXACTLY
namespace YourApp.Application.DTOs;

public record ToolSearchResultDto
{
    public List<ToolSearchItemDto> Tools { get; init; } = new();
    public int TotalCount { get; init; }
    public bool HasMore { get; init; }
    public string? SearchQuery { get; init; }
    public AppliedFiltersDto AppliedFilters { get; init; } = new();
}

public record ToolSearchItemDto
{
    public Guid Id { get; init; }
    public string Title { get; init; } = null!;
    public string Description { get; init; } = null!;
    public string? Brand { get; init; }
    public string? Model { get; init; }
    public string Category { get; init; } = null!;
    public string Condition { get; init; } = null!;
    public decimal EstimatedValue { get; init; }
    public List<ToolPhotoDto> Photos { get; init; } = new();
    public ToolOwnerDto Owner { get; init; } = null!;
    public bool IsAvailable { get; init; }
    public double DistanceMiles { get; init; }
    public string ApproximateLocation { get; init; } = null!;
}

public record ToolOwnerDto
{
    public Guid Id { get; init; }
    public string Name { get; init; } = null!;
    public string? PhotoUrl { get; init; }
}

public record AppliedFiltersDto
{
    public double MaxDistanceMiles { get; init; }
    public bool AvailableOnly { get; init; }
    public List<string> Conditions { get; init; } = new();
    public List<string> Categories { get; init; } = new();
}

public record ToolSuggestionDto
{
    public string Title { get; init; } = null!;
    public string Category { get; init; } = null!;
    public int Count { get; init; }
}
```
::DTO

---

## VALIDATION

### VALIDATOR::ToolSearchRequestValidator
FILE: src/Application/Validators/ToolSearchRequestValidator.cs
```csharp
// COPY THIS EXACTLY
using FluentValidation;
using YourApp.Application.DTOs;
using YourApp.Domain.Enums;

namespace YourApp.Application.Validators;

public class ToolSearchRequestValidator : AbstractValidator<ToolSearchRequest>
{
    public ToolSearchRequestValidator()
    {
        RuleFor(x => x.Query)
            .MaximumLength(100)
            .WithMessage("Search query cannot exceed 100 characters");

        RuleFor(x => x.MaxDistanceMiles)
            .InclusiveBetween(0.5, 5.0)
            .WithMessage("Maximum distance must be between 0.5 and 5 miles");

        RuleFor(x => x.PageSize)
            .InclusiveBetween(1, 50)
            .WithMessage("Page size must be between 1 and 50");

        RuleFor(x => x.Page)
            .GreaterThan(0)
            .WithMessage("Page must be greater than 0");

        RuleForEach(x => x.Conditions)
            .Must(BeValidCondition)
            .WithMessage("Invalid tool condition specified");

        RuleForEach(x => x.Categories)
            .Must(BeValidCategory)
            .WithMessage("Invalid tool category specified");
    }

    private bool BeValidCondition(string condition)
    {
        return Enum.TryParse<ToolCondition>(condition, ignoreCase: true, out _);
    }

    private bool BeValidCategory(string category)
    {
        return Enum.TryParse<ToolCategory>(category, ignoreCase: true, out _);
    }
}
```
::VALIDATOR

---

## FRONTEND_API_CLIENT

### API_CLIENT::toolSearchApi
FILE: src/Web/src/api/toolSearchApi.ts
```typescript
// COPY THIS EXACTLY
import { apiClient } from './apiClient';

export interface ToolSearchRequest {
  query?: string;
  maxDistanceMiles?: number;
  availableOnly?: boolean;
  conditions?: string[];
  categories?: string[];
  pageSize?: number;
  page?: number;
}

export interface ToolSearchResult {
  tools: ToolSearchItem[];
  totalCount: number;
  hasMore: boolean;
  searchQuery?: string;
  appliedFilters: AppliedFilters;
}

export interface ToolSearchItem {
  id: string;
  title: string;
  description: string;
  brand?: string;
  model?: string;
  category: string;
  condition: string;
  estimatedValue: number;
  photos: ToolPhoto[];
  owner: ToolOwner;
  isAvailable: boolean;
  distanceMiles: number;
  approximateLocation: string;
}

export interface ToolPhoto {
  id: string;
  photoUrl: string;
  photoOrder: number;
}

export interface ToolOwner {
  id: string;
  name: string;
  photoUrl?: string;
}

export interface AppliedFilters {
  maxDistanceMiles: number;
  availableOnly: boolean;
  conditions: string[];
  categories: string[];
}

export interface ToolSuggestion {
  title: string;
  category: string;
  count: number;
}

export const toolSearchApi = {
  searchTools: async (request: ToolSearchRequest): Promise<ToolSearchResult> => {
    const params = new URLSearchParams();
    
    if (request.query) params.append('query', request.query);
    if (request.maxDistanceMiles) params.append('maxDistance', request.maxDistanceMiles.toString());
    if (request.availableOnly !== undefined)