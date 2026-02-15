# Tool Inventory Management - Implementation Specification

META::
  type: feature
  component: tool-inventory
  dependencies: foundation
  tech_stack: ASP.NET Core 8, React 18, PostgreSQL
  estimated_effort_hours: 45
::META

---

## IMPLEMENTATION_ORDER

STEP_1: Database entities and configurations (Tools, ToolPhotos)
STEP_2: Domain models and enums
STEP_3: Repository interfaces and implementations  
STEP_4: Service layer (ToolService, PhotoUploadService)
STEP_5: API controllers (ToolsController, PhotosController)
STEP_6: DTOs and validation
STEP_7: Frontend API client
STEP_8: Frontend components (ToolForm, ToolList, PhotoUpload)
STEP_9: Unit tests
STEP_10: Integration tests

---

## DATABASE_SCHEMA

### TABLE::Tools
```sql
CREATE TABLE "Tools" (
    "Id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "OwnerId" uuid NOT NULL REFERENCES "Users"("Id") ON DELETE CASCADE,
    "Title" varchar(150) NOT NULL,
    "Description" text NOT NULL,
    "Brand" varchar(50) NULL,
    "Model" varchar(50) NULL,
    "Category" varchar(50) NOT NULL,
    "EstimatedValue" integer NOT NULL,
    "YearPurchased" integer NULL,
    "Condition" varchar(20) NOT NULL DEFAULT 'Good',
    "SpecialInstructions" text NULL,
    "MaxLoanDurationDays" integer NOT NULL DEFAULT 7,
    "DepositRequired" boolean NOT NULL DEFAULT false,
    "IsAvailable" boolean NOT NULL DEFAULT true,
    "IsDeleted" boolean NOT NULL DEFAULT false,
    "CreatedAt" timestamp with time zone NOT NULL DEFAULT now(),
    "UpdatedAt" timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX "IX_Tools_OwnerId" ON "Tools"("OwnerId");
CREATE INDEX "IX_Tools_Category_Available" ON "Tools"("Category", "IsAvailable") WHERE "IsDeleted" = false;
CREATE INDEX "IX_Tools_Search" ON "Tools" USING gin(to_tsvector('english', "Title" || ' ' || "Description")) WHERE "IsDeleted" = false AND "IsAvailable" = true;
```
::TABLE

### TABLE::ToolPhotos
```sql
CREATE TABLE "ToolPhotos" (
    "Id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "ToolId" uuid NOT NULL REFERENCES "Tools"("Id") ON DELETE CASCADE,
    "PhotoUrl" varchar(2048) NOT NULL,
    "PhotoOrder" integer NOT NULL DEFAULT 0,
    "UploadedAt" timestamp with time zone NOT NULL DEFAULT now(),
    "IsDeleted" boolean NOT NULL DEFAULT false
);

CREATE INDEX "IX_ToolPhotos_ToolId_Order" ON "ToolPhotos"("ToolId", "PhotoOrder") WHERE "IsDeleted" = false;
```
::TABLE

### MIGRATION::20260216_CreateTools
```csharp
public partial class CreateTools : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        // COPY THIS EXACTLY
        migrationBuilder.CreateTable(
            name: "Tools",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                OwnerId = table.Column<Guid>(type: "uuid", nullable: false),
                Title = table.Column<string>(type: "character varying(150)", maxLength: 150, nullable: false),
                Description = table.Column<string>(type: "text", nullable: false),
                Brand = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                Model = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                Category = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                EstimatedValue = table.Column<int>(type: "integer", nullable: false),
                YearPurchased = table.Column<int>(type: "integer", nullable: true),
                Condition = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false, defaultValue: "Good"),
                SpecialInstructions = table.Column<string>(type: "text", nullable: true),
                MaxLoanDurationDays = table.Column<int>(type: "integer", nullable: false, defaultValue: 7),
                DepositRequired = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                IsAvailable = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                IsDeleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()"),
                UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()")
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_Tools", x => x.Id);
                table.ForeignKey(
                    name: "FK_Tools_Users_OwnerId",
                    column: x => x.OwnerId,
                    principalTable: "Users",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
            });

        migrationBuilder.CreateTable(
            name: "ToolPhotos",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                ToolId = table.Column<Guid>(type: "uuid", nullable: false),
                PhotoUrl = table.Column<string>(type: "character varying(2048)", maxLength: 2048, nullable: false),
                PhotoOrder = table.Column<int>(type: "integer", nullable: false, defaultValue: 0),
                UploadedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()"),
                IsDeleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_ToolPhotos", x => x.Id);
                table.ForeignKey(
                    name: "FK_ToolPhotos_Tools_ToolId",
                    column: x => x.ToolId,
                    principalTable: "Tools",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
            });

        migrationBuilder.CreateIndex(
            name: "IX_Tools_OwnerId",
            table: "Tools",
            column: "OwnerId");

        migrationBuilder.CreateIndex(
            name: "IX_Tools_Category_Available",
            table: "Tools",
            columns: new[] { "Category", "IsAvailable" },
            filter: "\"IsDeleted\" = false");

        migrationBuilder.CreateIndex(
            name: "IX_ToolPhotos_ToolId_Order",
            table: "ToolPhotos",
            columns: new[] { "ToolId", "PhotoOrder" },
            filter: "\"IsDeleted\" = false");

        migrationBuilder.Sql(@"
            CREATE INDEX ""IX_Tools_Search"" ON ""Tools"" 
            USING gin(to_tsvector('english', ""Title"" || ' ' || ""Description"")) 
            WHERE ""IsDeleted"" = false AND ""IsAvailable"" = true;
        ");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "ToolPhotos");
        migrationBuilder.DropTable(name: "Tools");
    }
}
```
::MIGRATION

---

## DOMAIN_ENTITIES

### ENTITY::Tool
FILE: src/Domain/Entities/Tool.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
using System;
using System.Collections.Generic;
using YourApp.Domain.Enums;

namespace YourApp.Domain.Entities;

public class Tool
{
    public Guid Id { get; init; }
    public Guid OwnerId { get; init; }
    public string Title { get; set; } = null!;
    public string Description { get; set; } = null!;
    public string? Brand { get; set; }
    public string? Model { get; set; }
    public ToolCategory Category { get; set; }
    public int EstimatedValue { get; set; }
    public int? YearPurchased { get; set; }
    public ToolCondition Condition { get; set; } = ToolCondition.Good;
    public string? SpecialInstructions { get; set; }
    public int MaxLoanDurationDays { get; set; } = 7;
    public bool DepositRequired { get; set; } = false;
    public bool IsAvailable { get; set; } = true;
    public bool IsDeleted { get; set; } = false;
    public DateTime CreatedAt { get; init; }
    public DateTime UpdatedAt { get; set; }
    
    // Navigation properties
    public User Owner { get; init; } = null!;
    public ICollection<ToolPhoto> Photos { get; init; } = new List<ToolPhoto>();
}
```
::ENTITY

### ENTITY::ToolPhoto
FILE: src/Domain/Entities/ToolPhoto.cs
```csharp
// COPY THIS EXACTLY
using System;

namespace YourApp.Domain.Entities;

public class ToolPhoto
{
    public Guid Id { get; init; }
    public Guid ToolId { get; init; }
    public string PhotoUrl { get; set; } = null!;
    public int PhotoOrder { get; set; } = 0;
    public DateTime UploadedAt { get; init; }
    public bool IsDeleted { get; set; } = false;
    
    // Navigation properties
    public Tool Tool { get; init; } = null!;
}
```
::ENTITY

### ENUM::ToolCategory
FILE: src/Domain/Enums/ToolCategory.cs
```csharp
// COPY THIS EXACTLY
namespace YourApp.Domain.Enums;

public enum ToolCategory
{
    PowerTools,
    HandTools,
    GardenTools,
    AutoTools,
    HomeImprovement,
    Electrical,
    Plumbing,
    Painting,
    MeasuringTools,
    SafetyEquipment,
    CleaningEquipment,
    Other
}
```
::ENUM

### ENUM::ToolCondition
FILE: src/Domain/Enums/ToolCondition.cs
```csharp
// COPY THIS EXACTLY
namespace YourApp.Domain.Enums;

public enum ToolCondition
{
    Excellent,
    Good,
    Fair,
    NeedsRepair
}
```
::ENUM

---

## EF_CORE_CONFIGURATIONS

### CONFIG::ToolConfiguration
FILE: src/Infrastructure/Data/Configurations/ToolConfiguration.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using YourApp.Domain.Entities;
using YourApp.Domain.Enums;

namespace YourApp.Infrastructure.Data.Configurations;

public class ToolConfiguration : IEntityTypeConfiguration<Tool>
{
    public void Configure(EntityTypeBuilder<Tool> builder)
    {
        builder.ToTable("Tools");
        
        builder.HasKey(x => x.Id);
        
        builder.Property(x => x.OwnerId)
            .IsRequired();
        
        builder.Property(x => x.Title)
            .IsRequired()
            .HasMaxLength(150);
        
        builder.Property(x => x.Description)
            .IsRequired();
        
        builder.Property(x => x.Brand)
            .HasMaxLength(50);
        
        builder.Property(x => x.Model)
            .HasMaxLength(50);
        
        builder.Property(x => x.Category)
            .IsRequired()
            .HasMaxLength(50)
            .HasConversion<string>();
        
        builder.Property(x => x.EstimatedValue)
            .IsRequired();
        
        builder.Property(x => x.Condition)
            .IsRequired()
            .HasMaxLength(20)
            .HasConversion<string>()
            .HasDefaultValue(ToolCondition.Good);
        
        builder.Property(x => x.MaxLoanDurationDays)
            .IsRequired()
            .HasDefaultValue(7);
        
        builder.Property(x => x.DepositRequired)
            .IsRequired()
            .HasDefaultValue(false);
        
        builder.Property(x => x.IsAvailable)
            .IsRequired()
            .HasDefaultValue(true);
        
        builder.Property(x => x.IsDeleted)
            .IsRequired()
            .HasDefaultValue(false);
        
        builder.Property(x => x.CreatedAt)
            .IsRequired()
            .HasDefaultValueSql("now()");
        
        builder.Property(x => x.UpdatedAt)
            .IsRequired()
            .HasDefaultValueSql("now()");
        
        builder.HasIndex(x => x.OwnerId);
        builder.HasIndex(x => new { x.Category, x.IsAvailable })
            .HasFilter("\"IsDeleted\" = false");
        
        // Relationships
        builder.HasOne(x => x.Owner)
            .WithMany()
            .HasForeignKey(x => x.OwnerId)
            .OnDelete(DeleteBehavior.Cascade);
        
        builder.HasMany(x => x.Photos)
            .WithOne(x => x.Tool)
            .HasForeignKey(x => x.ToolId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
```
::CONFIG

### CONFIG::ToolPhotoConfiguration
FILE: src/Infrastructure/Data/Configurations/ToolPhotoConfiguration.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using YourApp.Domain.Entities;

namespace YourApp.Infrastructure.Data.Configurations;

public class ToolPhotoConfiguration : IEntityTypeConfiguration<ToolPhoto>
{
    public void Configure(EntityTypeBuilder<ToolPhoto> builder)
    {
        builder.ToTable("ToolPhotos");
        
        builder.HasKey(x => x.Id);
        
        builder.Property(x => x.ToolId)
            .IsRequired();
        
        builder.Property(x => x.PhotoUrl)
            .IsRequired()
            .HasMaxLength(2048);
        
        builder.Property(x => x.PhotoOrder)
            .IsRequired()
            .HasDefaultValue(0);
        
        builder.Property(x => x.UploadedAt)
            .IsRequired()
            .HasDefaultValueSql("now()");
        
        builder.Property(x => x.IsDeleted)
            .IsRequired()
            .HasDefaultValue(false);
        
        builder.HasIndex(x => new { x.ToolId, x.PhotoOrder })
            .HasFilter("\"IsDeleted\" = false");
        
        // Relationships
        builder.HasOne(x => x.Tool)
            .WithMany(x => x.Photos)
            .HasForeignKey(x => x.ToolId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
```
::CONFIG

---

## API_ENDPOINTS

### ENDPOINT::POST_/api/v1/tools
REQUEST:
```json
{
  "title": "Makita Cordless Drill",
  "description": "18V cordless drill with two batteries. Great for home projects. Please return with both batteries charged.",
  "brand": "Makita",
  "model": "XPH102",
  "category": "PowerTools",
  "estimatedValue": 150,
  "yearPurchased": 2022,
  "condition": "Good",
  "specialInstructions": "Charger is in the case. Please charge batteries after use.",
  "maxLoanDurationDays": 7,
  "depositRequired": false
}
```

RESPONSE_201:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Makita Cordless Drill",
  "description": "18V cordless drill with two batteries...",
  "brand": "Makita",
  "model": "XPH102",
  "category": "PowerTools",
  "estimatedValue": 150,
  "yearPurchased": 2022,
  "condition": "Good",
  "specialInstructions": "Charger is in the case...",
  "maxLoanDurationDays": 7,
  "depositRequired": false,
  "isAvailable": true,
  "photos": [],
  "createdAt": "2026-02-16T10:30:00Z",
  "updatedAt": "2026-02-16T10:30:00Z"
}
```

RESPONSE_400:
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "Validation failed",
  "status": 400,
  "errors": {
    "Title": ["Title must be between 5 and 150 characters"],
    "EstimatedValue": ["Estimated value must be between $1 and $10,000"]
  }
}
```

CONTROLLER:
FILE: src/API/Controllers/ToolsController.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using YourApp.Application.DTOs;
using YourApp.Application.Services;
using System.Security.Claims;

namespace YourApp.API.Controllers;

[ApiController]
[Route("api/v1/tools")]
[Authorize]
public class ToolsController : ControllerBase
{
    private readonly IToolService _toolService;
    
    public ToolsController(IToolService toolService)
    {
        _toolService = toolService;
    }
    
    [HttpPost]
    [ProducesResponseType(typeof(ToolDto), 201)]
    [ProducesResponseType(typeof(ProblemDetails), 400)]
    public async Task<ActionResult<ToolDto>> CreateTool([FromBody] CreateToolRequest request)
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)?.Value!);
        var tool = await _toolService.CreateToolAsync(userId, request);
        return CreatedAtAction(nameof(GetTool), new { id = tool.Id }, tool);
    }
    
    [HttpGet("{id}")]
    [ProducesResponseType(typeof(ToolDto), 200)]
    [ProducesResponseType(404)]
    public async Task<ActionResult<ToolDto>> GetTool(Guid id)
    {
        var tool = await _toolService.GetToolByIdAsync(id);
        if (tool == null) return NotFound();
        return Ok(tool);
    }
    
    [HttpGet("my-tools")]
    [ProducesResponseType(typeof(List<ToolSummaryDto>), 200)]
    public async Task<ActionResult<List<ToolSummaryDto>>> GetMyTools()
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)?.Value!);
        var tools = await _toolService.GetUserToolsAsync(userId);
        return Ok(tools);
    }
    
    [HttpPut("{id}")]
    [ProducesResponseType(typeof(ToolDto), 200)]
    [ProducesResponseType(404)]
    [ProducesResponseType(403)]
    public async Task<ActionResult<ToolDto>> UpdateTool(Guid id, [FromBody] UpdateToolRequest request)
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)?.Value!);
        
        try
        {
            var tool = await _toolService.UpdateToolAsync(userId, id, request);
            return Ok(tool);
        }
        catch (ToolNotFoundException)
        {
            return NotFound();
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
    }
    
    [HttpPatch("{id}/availability")]
    [ProducesResponseType(204)]
    [ProducesResponseType(404)]
    [ProducesResponseType(403)]
    public async Task<IActionResult> UpdateAvailability(Guid id, [FromBody] UpdateAvailabilityRequest request)
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)?.Value!);
        
        try
        {
            await _toolService.UpdateAvailabilityAsync(userId, id, request.IsAvailable);
            return NoContent();
        }
        catch (ToolNotFoundException)
        {
            return NotFound();
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
    }
    
    [HttpDelete("{id}")]
    [ProducesResponseType(204)]
    [ProducesResponseType(404)]
    [ProducesResponseType(403)]
    public async Task<IActionResult> DeleteTool(Guid id)
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)?.Value!);
        
        try
        {
            await _toolService.DeleteToolAsync(userId, id);
            return NoContent();
        }
        catch (ToolNotFoundException)
        {
            return NotFound();
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
    }
}
```
::ENDPOINT

### ENDPOINT::POST_/api/v1/tools/{id}/photos
REQUEST: (multipart/form-data)
```
file: [binary image data]
```

RESPONSE_201:
```json
{
  "id": "456e7890-e89b-12d3-a456-426614174000",
  "photoUrl": "https://storage.example.com/tools/123e4567/photo-1.jpg",
  "photoOrder": 0,
  "uploadedAt": "2026-02-16T10:35:00Z"
}
```

RESPONSE_400:
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "Photo upload failed",
  "status": 400,
  "detail": "File size exceeds maximum allowed (5MB)"
}
```

CONTROLLER:
FILE: src/API/Controllers/PhotosController.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using YourApp.Application.DTOs;
using YourApp.Application.Services;
using System.Security.Claims;

namespace YourApp.API.Controllers;

[ApiController]
[Route("api/v1/tools/{toolId}/photos")]
[Authorize]
public class PhotosController : ControllerBase
{
    private readonly IToolPhotoService _photoService;
    
    public PhotosController(IToolPhotoService photoService)
    {
        _photoService = photoService;
    }
    
    [HttpPost]
    [ProducesResponseType(typeof(ToolPhotoDto), 201)]
    [ProducesResponseType(typeof(ProblemDetails), 400)]
    [ProducesResponseType(403)]
    public async Task<ActionResult<ToolPhotoDto>> UploadPhoto(Guid toolId, IFormFile file)
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)?.Value!);
        
        try
        {
            var photo = await _photoService.UploadPhotoAsync(userId, toolId, file);
            return CreatedAtAction(nameof(GetPhoto), new { toolId, id = photo.Id }, photo);
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new ProblemDetails
            {
                Title = "Photo upload failed",
                Detail = ex.Message,
                Status = 400
            });
        }
    }
    
    [HttpGet("{id}")]
    [ProducesResponseType(typeof(ToolPhotoDto), 200)]
    [ProducesResponseType(404)]
    public async Task<ActionResult<ToolPhotoDto>> GetPhoto(Guid toolId, Guid id)
    {
        var photo = await _photoService.GetPhotoAsync(id);
        if (photo == null || photo.ToolId != toolId) return NotFound();
        return Ok(photo);
    }
    
    [HttpDelete("{id}")]
    [ProducesResponseType(204)]
    [ProducesResponseType(404)]
    [ProducesResponseType(403)]
    public async Task<IActionResult> DeletePhoto(Guid toolId, Guid id)
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)?.Value!);
        
        try
        {
            await _photoService.DeletePhotoAsync(userId, toolId, id);
            return NoContent();
        }
        catch (ToolNotFoundException)
        {
            return NotFound();
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
    }
    
    [HttpPut("{id}/order")]
    [ProducesResponseType(204)]
    [ProducesResponseType(404)]
    [ProducesResponseType(403)]
    public async Task<IActionResult> UpdatePhotoOrder(Guid toolId, Guid id, [FromBody] UpdatePhotoOrderRequest request)
    {
        var userId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)?.Value!);
        
        try
        {
            await _photoService.UpdatePhotoOrderAsync(userId, toolId, id, request.PhotoOrder);
            return NoContent();
        }
        catch (ToolNotFoundException)
        {
            return NotFound();
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
    }
}
```
::ENDPOINT

---

## SERVICE_LAYER

### INTERFACE::IToolService
FILE: src/Application/Services/IToolService.cs
```csharp
// COPY THIS EXACTLY
using YourApp.Application.DTOs;

namespace YourApp.Application.Services;

public interface IToolService
{
    Task<ToolDto> CreateToolAsync(Guid userId, CreateToolRequest request);
    Task<ToolDto?> GetToolByIdAsync(Guid id);
    Task<List<ToolSummaryDto>> GetUserToolsAsync(Guid userId);
    Task<ToolDto> UpdateToolAsync(Guid userId, Guid toolId, UpdateToolRequest request);
    Task UpdateAvailabilityAsync(Guid userId, Guid toolId, bool isAvailable);
    Task DeleteToolAsync(Guid userId, Guid toolId);
    Task<List<string>> CheckDuplicateTitlesAsync(Guid userId, string title);
}
```
::INTERFACE

### INTERFACE::IToolPhotoService
FILE: src/Application/Services/IToolPhotoService.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.AspNetCore.Http;
using YourApp.Application.DTOs;

namespace YourApp.Application.Services;

public interface IToolPhotoService
{
    Task<ToolPhotoDto> UploadPhotoAsync(Guid userId, Guid toolId, IFormFile file);
    Task<ToolPhotoDto?> GetPhotoAsync(Guid photoId);
    Task DeletePhotoAsync(Guid userId, Guid toolId, Guid photoId);
    Task UpdatePhotoOrderAsync(Guid userId, Guid toolId, Guid photoId, int newOrder);
}
```
::INTERFACE

### IMPLEMENTATION::ToolService
FILE: src/Infrastructure/Services/ToolService.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.EntityFrameworkCore;
using YourApp.Application.DTOs;
using YourApp.Application.Services;
using YourApp.Domain.Entities;
using YourApp.Domain.Enums;
using YourApp.Infrastructure.Data;

namespace YourApp.Infrastructure.Services;

public class ToolService : IToolService
{
    private readonly ApplicationDbContext _context;
    
    public ToolService(ApplicationDbContext context)
    {
        _context = context;
    }
    
    public async Task<ToolDto> CreateToolAsync(Guid userId, CreateToolRequest request)
    {
        // VALIDATION: Check for duplicate titles and warn user
        var duplicates = await CheckDuplicateTitlesAsync(userId, request.Title);
        
        // CREATE: Build new tool entity
        var tool = new Tool
        {
            OwnerId = userId,
            Title = request.Title,
            Description = request.Description,
            Brand = request.Brand,
            Model = request.Model,
            Category = request.Category,
            EstimatedValue = request.EstimatedValue,
            YearPurchased = request.YearPurchased,
            Condition = request.Condition,
            SpecialInstructions = request.SpecialInstructions,
            MaxLoanDurationDays = request.MaxLoanDurationDays,
            DepositRequired = request.DepositRequired,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };
        
        _context.Tools.Add(tool);
        await _context.SaveChangesAsync();
        
        // RETURN: Load with navigation properties for DTO mapping
        var createdTool = await _context.Tools
            .Include(t => t.Photos.Where(p => !p.IsDeleted))
            .Include(t => t.Owner)
            .FirstAsync(t => t.Id == tool.Id);
        
        return MapToToolDto(createdTool);
    }
    
    public async Task<ToolDto?> GetToolByIdAsync(Guid id)
    {
        var tool = await _context.Tools
            .AsNoTracking()
            .Include(t => t.Photos.Where(p => !p.IsDeleted))
            .Include(t => t.Owner)
            .FirstOrDefaultAsync(t => t.Id == id && !t.IsDeleted);
        
        return tool == null ? null : MapToToolDto(tool);
    }
    
    public async Task<List<ToolSummaryDto>> GetUserToolsAsync(Guid userId)
    {
        var tools = await _context.Tools
            .AsNoTracking()
            .Include(t => t.Photos.Where(p => !p.IsDeleted))
            .Where(t => t.OwnerId == userId && !t.IsDeleted)
            .OrderByDescending(t => t.CreatedAt)
            .ToListAsync();
        
        return tools.Select(MapToToolSummaryDto).ToList();
    }
    
    public async Task<ToolDto> UpdateToolAsync(Guid userId,