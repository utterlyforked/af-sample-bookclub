# Borrowing Request System - Implementation Specification

META::
  type: feature
  component: borrowing-request-system
  dependencies: user-management, tool-inventory, photo-service, email-service, api-infrastructure
  tech_stack: ASP.NET Core, React TypeScript, PostgreSQL
  estimated_effort_hours: 50
::META

---

## IMPLEMENTATION_ORDER

STEP_1: Database schema and migrations for BorrowRequest and RequestMessage
STEP_2: Domain entities (BorrowRequest, RequestMessage, enums)
STEP_3: EF Core configurations for new entities
STEP_4: DTOs and validation models
STEP_5: Repository interfaces and implementations
STEP_6: Service layer (BorrowRequestService, RequestMessageService)
STEP_7: Background job for request expiration
STEP_8: API controllers (BorrowRequestsController, RequestMessagesController)
STEP_9: Email notification service integration
STEP_10: Frontend API clients
STEP_11: Frontend components (request form, request list, message thread)
STEP_12: Unit tests
STEP_13: Integration tests

---

## DATABASE_SCHEMA

### TABLE::BorrowRequests
```sql
CREATE TYPE borrow_request_status AS ENUM (
    'pending',
    'counter_proposed', 
    'awaiting_borrower_response',
    'approved',
    'declined',
    'expired'
);

CREATE TABLE "BorrowRequests" (
    "Id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "ToolId" uuid NOT NULL REFERENCES "Tools"("Id") ON DELETE CASCADE,
    "BorrowerId" uuid NOT NULL REFERENCES "Users"("Id") ON DELETE CASCADE,
    "RequestedStartDate" date NOT NULL,
    "RequestedEndDate" date NOT NULL,
    "IntendedUse" varchar(500) NOT NULL,
    "PickupTimePreference" varchar(20) NULL CHECK ("PickupTimePreference" IN ('morning', 'afternoon', 'evening')),
    "SpecialRequests" varchar(200) NULL,
    "Status" borrow_request_status NOT NULL DEFAULT 'pending',
    "CounterProposalStartDate" date NULL,
    "CounterProposalEndDate" date NULL,
    "CounterProposalMessage" varchar(300) NULL,
    "ResponseMessage" varchar(300) NULL,
    "CreatedAt" timestamp with time zone NOT NULL DEFAULT now(),
    "UpdatedAt" timestamp with time zone NOT NULL DEFAULT now(),
    "ExpiresAt" timestamp with time zone NOT NULL,
    "RespondedAt" timestamp with time zone NULL
);

CREATE INDEX "IX_BorrowRequests_ToolId" ON "BorrowRequests"("ToolId");
CREATE INDEX "IX_BorrowRequests_BorrowerId" ON "BorrowRequests"("BorrowerId");
CREATE INDEX "IX_BorrowRequests_Status" ON "BorrowRequests"("Status");
CREATE INDEX "IX_BorrowRequests_ExpiresAt" ON "BorrowRequests"("ExpiresAt") WHERE "Status" IN ('pending', 'counter_proposed');
CREATE INDEX "IX_BorrowRequests_DateRange" ON "BorrowRequests"("RequestedStartDate", "RequestedEndDate") WHERE "Status" = 'pending';

-- Constraint: No overlapping pending requests for same tool
CREATE UNIQUE INDEX "UX_BorrowRequests_NoOverlapping" ON "BorrowRequests"("ToolId") 
WHERE "Status" IN ('pending', 'counter_proposed', 'approved');

-- Constraint: One active request per borrower per tool
CREATE UNIQUE INDEX "UX_BorrowRequests_OneBorrowerPerTool" ON "BorrowRequests"("ToolId", "BorrowerId") 
WHERE "Status" IN ('pending', 'counter_proposed');
```
::TABLE

### TABLE::RequestMessages
```sql
CREATE TABLE "RequestMessages" (
    "Id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "BorrowRequestId" uuid NOT NULL REFERENCES "BorrowRequests"("Id") ON DELETE CASCADE,
    "SenderId" uuid NOT NULL REFERENCES "Users"("Id") ON DELETE CASCADE,
    "MessageText" varchar(1000) NOT NULL,
    "SentAt" timestamp with time zone NOT NULL DEFAULT now(),
    "IsSystemMessage" boolean NOT NULL DEFAULT false
);

CREATE INDEX "IX_RequestMessages_BorrowRequestId_SentAt" ON "RequestMessages"("BorrowRequestId", "SentAt");
CREATE INDEX "IX_RequestMessages_SenderId" ON "RequestMessages"("SenderId");
```
::TABLE

### TABLE::RequestMessageAttachments
```sql
CREATE TABLE "RequestMessageAttachments" (
    "Id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "MessageId" uuid NOT NULL REFERENCES "RequestMessages"("Id") ON DELETE CASCADE,
    "PhotoUrl" varchar(2048) NOT NULL,
    "OriginalFileName" varchar(256) NOT NULL,
    "FileSizeBytes" integer NOT NULL,
    "UploadedAt" timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX "IX_RequestMessageAttachments_MessageId" ON "RequestMessageAttachments"("MessageId");
```
::TABLE

### MIGRATION::20260216_CreateBorrowRequestSystem
```csharp
public partial class CreateBorrowRequestSystem : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        // Create enum type
        migrationBuilder.Sql(@"
            CREATE TYPE borrow_request_status AS ENUM (
                'pending',
                'counter_proposed', 
                'awaiting_borrower_response',
                'approved',
                'declined',
                'expired'
            );
        ");

        // Create BorrowRequests table
        migrationBuilder.CreateTable(
            name: "BorrowRequests",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                ToolId = table.Column<Guid>(type: "uuid", nullable: false),
                BorrowerId = table.Column<Guid>(type: "uuid", nullable: false),
                RequestedStartDate = table.Column<DateOnly>(type: "date", nullable: false),
                RequestedEndDate = table.Column<DateOnly>(type: "date", nullable: false),
                IntendedUse = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                PickupTimePreference = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                SpecialRequests = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                Status = table.Column<string>(type: "borrow_request_status", nullable: false, defaultValue: "pending"),
                CounterProposalStartDate = table.Column<DateOnly>(type: "date", nullable: true),
                CounterProposalEndDate = table.Column<DateOnly>(type: "date", nullable: true),
                CounterProposalMessage = table.Column<string>(type: "character varying(300)", maxLength: 300, nullable: true),
                ResponseMessage = table.Column<string>(type: "character varying(300)", maxLength: 300, nullable: true),
                CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()"),
                UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()"),
                ExpiresAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                RespondedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_BorrowRequests", x => x.Id);
                table.ForeignKey(
                    name: "FK_BorrowRequests_Tools_ToolId",
                    column: x => x.ToolId,
                    principalTable: "Tools",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
                table.ForeignKey(
                    name: "FK_BorrowRequests_Users_BorrowerId",
                    column: x => x.BorrowerId,
                    principalTable: "Users",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
                table.CheckConstraint(
                    "CK_BorrowRequests_PickupTimePreference",
                    "\"PickupTimePreference\" IS NULL OR \"PickupTimePreference\" IN ('morning', 'afternoon', 'evening')");
            });

        // Create RequestMessages table
        migrationBuilder.CreateTable(
            name: "RequestMessages",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                BorrowRequestId = table.Column<Guid>(type: "uuid", nullable: false),
                SenderId = table.Column<Guid>(type: "uuid", nullable: false),
                MessageText = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: false),
                SentAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()"),
                IsSystemMessage = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_RequestMessages", x => x.Id);
                table.ForeignKey(
                    name: "FK_RequestMessages_BorrowRequests_BorrowRequestId",
                    column: x => x.BorrowRequestId,
                    principalTable: "BorrowRequests",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
                table.ForeignKey(
                    name: "FK_RequestMessages_Users_SenderId",
                    column: x => x.SenderId,
                    principalTable: "Users",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
            });

        // Create RequestMessageAttachments table
        migrationBuilder.CreateTable(
            name: "RequestMessageAttachments",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                MessageId = table.Column<Guid>(type: "uuid", nullable: false),
                PhotoUrl = table.Column<string>(type: "character varying(2048)", maxLength: 2048, nullable: false),
                OriginalFileName = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: false),
                FileSizeBytes = table.Column<int>(type: "integer", nullable: false),
                UploadedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()")
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_RequestMessageAttachments", x => x.Id);
                table.ForeignKey(
                    name: "FK_RequestMessageAttachments_RequestMessages_MessageId",
                    column: x => x.MessageId,
                    principalTable: "RequestMessages",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
            });

        // Create indexes
        migrationBuilder.CreateIndex(
            name: "IX_BorrowRequests_ToolId",
            table: "BorrowRequests",
            column: "ToolId");

        migrationBuilder.CreateIndex(
            name: "IX_BorrowRequests_BorrowerId",
            table: "BorrowRequests",
            column: "BorrowerId");

        migrationBuilder.CreateIndex(
            name: "IX_BorrowRequests_Status",
            table: "BorrowRequests",
            column: "Status");

        migrationBuilder.CreateIndex(
            name: "IX_BorrowRequests_ExpiresAt",
            table: "BorrowRequests",
            column: "ExpiresAt",
            filter: "\"Status\" IN ('pending', 'counter_proposed')");

        migrationBuilder.CreateIndex(
            name: "IX_BorrowRequests_DateRange",
            table: "BorrowRequests",
            columns: new[] { "RequestedStartDate", "RequestedEndDate" },
            filter: "\"Status\" = 'pending'");

        migrationBuilder.CreateIndex(
            name: "UX_BorrowRequests_NoOverlapping",
            table: "BorrowRequests",
            column: "ToolId",
            unique: true,
            filter: "\"Status\" IN ('pending', 'counter_proposed', 'approved')");

        migrationBuilder.CreateIndex(
            name: "UX_BorrowRequests_OneBorrowerPerTool",
            table: "BorrowRequests",
            columns: new[] { "ToolId", "BorrowerId" },
            unique: true,
            filter: "\"Status\" IN ('pending', 'counter_proposed')");

        migrationBuilder.CreateIndex(
            name: "IX_RequestMessages_BorrowRequestId_SentAt",
            table: "RequestMessages",
            columns: new[] { "BorrowRequestId", "SentAt" });

        migrationBuilder.CreateIndex(
            name: "IX_RequestMessages_SenderId",
            table: "RequestMessages",
            column: "SenderId");

        migrationBuilder.CreateIndex(
            name: "IX_RequestMessageAttachments_MessageId",
            table: "RequestMessageAttachments",
            column: "MessageId");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "RequestMessageAttachments");
        migrationBuilder.DropTable(name: "RequestMessages");
        migrationBuilder.DropTable(name: "BorrowRequests");
        migrationBuilder.Sql("DROP TYPE IF EXISTS borrow_request_status;");
    }
}
```
::MIGRATION

---

## DOMAIN_ENTITIES

### ENTITY::BorrowRequestStatus
FILE: src/Domain/Enums/BorrowRequestStatus.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
namespace YourApp.Domain.Enums;

public enum BorrowRequestStatus
{
    Pending = 0,
    CounterProposed = 1,
    AwaitingBorrowerResponse = 2,
    Approved = 3,
    Declined = 4,
    Expired = 5
}
```
::ENTITY

### ENTITY::PickupTimePreference
FILE: src/Domain/Enums/PickupTimePreference.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
namespace YourApp.Domain.Enums;

public enum PickupTimePreference
{
    Morning = 0,
    Afternoon = 1,
    Evening = 2
}
```
::ENTITY

### ENTITY::BorrowRequest
FILE: src/Domain/Entities/BorrowRequest.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
using YourApp.Domain.Enums;

namespace YourApp.Domain.Entities;

public class BorrowRequest
{
    public Guid Id { get; init; }
    public Guid ToolId { get; init; }
    public Guid BorrowerId { get; init; }
    public DateOnly RequestedStartDate { get; init; }
    public DateOnly RequestedEndDate { get; init; }
    public string IntendedUse { get; init; } = null!;
    public PickupTimePreference? PickupTimePreference { get; init; }
    public string? SpecialRequests { get; init; }
    public BorrowRequestStatus Status { get; set; } = BorrowRequestStatus.Pending;
    public DateOnly? CounterProposalStartDate { get; set; }
    public DateOnly? CounterProposalEndDate { get; set; }
    public string? CounterProposalMessage { get; set; }
    public string? ResponseMessage { get; set; }
    public DateTime CreatedAt { get; init; }
    public DateTime UpdatedAt { get; set; }
    public DateTime ExpiresAt { get; set; }
    public DateTime? RespondedAt { get; set; }

    // Navigation properties
    public Tool Tool { get; init; } = null!;
    public User Borrower { get; init; } = null!;
    public ICollection<RequestMessage> Messages { get; init; } = new List<RequestMessage>();

    // Helper properties
    public User ToolOwner => Tool.Owner;
    public bool IsExpired => DateTime.UtcNow > ExpiresAt;
    public bool CanBeModified => Status is BorrowRequestStatus.Pending or BorrowRequestStatus.CounterProposed;
    
    // Business methods
    public void Approve(string? responseMessage = null)
    {
        if (Status != BorrowRequestStatus.Pending && Status != BorrowRequestStatus.CounterProposed)
            throw new InvalidOperationException($"Cannot approve request in status {Status}");
            
        Status = BorrowRequestStatus.Approved;
        ResponseMessage = responseMessage;
        RespondedAt = DateTime.UtcNow;
        UpdatedAt = DateTime.UtcNow;
    }

    public void Decline(string? responseMessage = null)
    {
        if (!CanBeModified)
            throw new InvalidOperationException($"Cannot decline request in status {Status}");
            
        Status = BorrowRequestStatus.Declined;
        ResponseMessage = responseMessage;
        RespondedAt = DateTime.UtcNow;
        UpdatedAt = DateTime.UtcNow;
    }

    public void CounterPropose(DateOnly startDate, DateOnly endDate, string message)
    {
        if (Status != BorrowRequestStatus.Pending)
            throw new InvalidOperationException($"Cannot counter-propose request in status {Status}");
            
        Status = BorrowRequestStatus.CounterProposed;
        CounterProposalStartDate = startDate;
        CounterProposalEndDate = endDate;
        CounterProposalMessage = message;
        ExpiresAt = DateTime.UtcNow.AddHours(24); // 24 hour expiry for counter-proposals
        UpdatedAt = DateTime.UtcNow;
    }

    public void AcceptCounterProposal()
    {
        if (Status != BorrowRequestStatus.CounterProposed)
            throw new InvalidOperationException("No counter-proposal to accept");
            
        // Move counter-proposal to main request
        RequestedStartDate = CounterProposalStartDate!.Value;
        RequestedEndDate = CounterProposalEndDate!.Value;
        Status = BorrowRequestStatus.Approved;
        RespondedAt = DateTime.UtcNow;
        UpdatedAt = DateTime.UtcNow;
    }

    public void MarkExpired()
    {
        if (!CanBeModified)
            return;
            
        Status = BorrowRequestStatus.Expired;
        UpdatedAt = DateTime.UtcNow;
    }
}
```
::ENTITY

### ENTITY::RequestMessage
FILE: src/Domain/Entities/RequestMessage.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
namespace YourApp.Domain.Entities;

public class RequestMessage
{
    public Guid Id { get; init; }
    public Guid BorrowRequestId { get; init; }
    public Guid SenderId { get; init; }
    public string MessageText { get; init; } = null!;
    public DateTime SentAt { get; init; }
    public bool IsSystemMessage { get; init; } = false;

    // Navigation properties
    public BorrowRequest BorrowRequest { get; init; } = null!;
    public User Sender { get; init; } = null!;
    public ICollection<RequestMessageAttachment> Attachments { get; init; } = new List<RequestMessageAttachment>();
}
```
::ENTITY

### ENTITY::RequestMessageAttachment
FILE: src/Domain/Entities/RequestMessageAttachment.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
namespace YourApp.Domain.Entities;

public class RequestMessageAttachment
{
    public Guid Id { get; init; }
    public Guid MessageId { get; init; }
    public string PhotoUrl { get; init; } = null!;
    public string OriginalFileName { get; init; } = null!;
    public int FileSizeBytes { get; init; }
    public DateTime UploadedAt { get; init; }

    // Navigation properties
    public RequestMessage Message { get; init; } = null!;
}
```
::ENTITY

---

## EF_CORE_CONFIGURATIONS

### CONFIG::BorrowRequestConfiguration
FILE: src/Infrastructure/Data/Configurations/BorrowRequestConfiguration.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using YourApp.Domain.Entities;
using YourApp.Domain.Enums;

namespace YourApp.Infrastructure.Data.Configurations;

public class BorrowRequestConfiguration : IEntityTypeConfiguration<BorrowRequest>
{
    public void Configure(EntityTypeBuilder<BorrowRequest> builder)
    {
        builder.ToTable("BorrowRequests");
        
        builder.HasKey(x => x.Id);
        
        builder.Property(x => x.ToolId)
            .IsRequired();
        
        builder.Property(x => x.BorrowerId)
            .IsRequired();
        
        builder.Property(x => x.RequestedStartDate)
            .IsRequired()
            .HasColumnType("date");
        
        builder.Property(x => x.RequestedEndDate)
            .IsRequired()
            .HasColumnType("date");
        
        builder.Property(x => x.IntendedUse)
            .IsRequired()
            .HasMaxLength(500);
        
        builder.Property(x => x.PickupTimePreference)
            .HasMaxLength(20)
            .HasConversion<string>();
        
        builder.Property(x => x.SpecialRequests)
            .HasMaxLength(200);
        
        builder.Property(x => x.Status)
            .IsRequired()
            .HasDefaultValue(BorrowRequestStatus.Pending)
            .HasConversion<string>()
            .HasColumnType("borrow_request_status");
        
        builder.Property(x => x.CounterProposalStartDate)
            .HasColumnType("date");
        
        builder.Property(x => x.CounterProposalEndDate)
            .HasColumnType("date");
        
        builder.Property(x => x.CounterProposalMessage)
            .HasMaxLength(300);
        
        builder.Property(x => x.ResponseMessage)
            .HasMaxLength(300);
        
        builder.Property(x => x.CreatedAt)
            .IsRequired()
            .HasDefaultValueSql("now()");
        
        builder.Property(x => x.UpdatedAt)
            .IsRequired()
            .HasDefaultValueSql("now()");
        
        builder.Property(x => x.ExpiresAt)
            .IsRequired();
        
        builder.HasIndex(x => x.ToolId);
        builder.HasIndex(x => x.BorrowerId);
        builder.HasIndex(x => x.Status);
        builder.HasIndex(x => x.ExpiresAt)
            .HasFilter("\"Status\" IN ('pending', 'counter_proposed')");
        builder.HasIndex(x => new { x.RequestedStartDate, x.RequestedEndDate })
            .HasFilter("\"Status\" = 'pending'");
        
        // Relationships
        builder.HasOne(x => x.Tool)
            .WithMany()
            .HasForeignKey(x => x.ToolId)
            .OnDelete(DeleteBehavior.Cascade);
        
        builder.HasOne(x => x.Borrower)
            .WithMany()
            .HasForeignKey(x => x.BorrowerId)
            .OnDelete(DeleteBehavior.Cascade);
        
        builder.HasMany(x => x.Messages)
            .WithOne(x => x.BorrowRequest)
            .HasForeignKey(x => x.BorrowRequestId)
            .OnDelete(DeleteBehavior.Cascade);
        
        // Ignore navigation helper
        builder.Ignore(x => x.ToolOwner);
        builder.Ignore(x => x.IsExpired);
        builder.Ignore(x => x.CanBeModified);
    }
}
```
::CONFIG

### CONFIG::RequestMessageConfiguration
FILE: src/Infrastructure/Data/Configurations/RequestMessageConfiguration.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using YourApp.Domain.Entities;

namespace YourApp.Infrastructure.Data.Configurations;

public class RequestMessageConfiguration : IEntityTypeConfiguration<RequestMessage>
{
    public void Configure(EntityTypeBuilder<RequestMessage> builder)
    {
        builder.ToTable("RequestMessages");
        
        builder.HasKey(x => x.Id);
        
        builder.Property(x => x.BorrowRequestId)
            .IsRequired();
        
        builder.Property(x => x.SenderId)
            .IsRequired();
        
        builder.Property(x => x.MessageText)
            .IsRequired()
            .HasMaxLength(1000);
        
        builder.Property(x => x.SentAt)
            .IsRequired()
            .HasDefaultValueSql("now()");
        
        builder.Property(x => x.IsSystemMessage)
            .IsRequired()
            .HasDefaultValue(false);
        
        builder.HasIndex(x => new { x.BorrowRequestId, x.SentAt });
        builder.HasIndex(x => x.SenderId);
        
        // Relationships
        builder.HasOne(x => x.BorrowRequest)
            .WithMany(x => x.Messages)
            .HasForeignKey(x => x.BorrowRequestId)
            .OnDelete(DeleteBehavior.Cascade);
        
        builder.HasOne(x => x.Sender)
            .WithMany()
            .HasForeignKey(x => x.SenderId)
            .OnDelete(DeleteBehavior.Cascade);
        
        builder.HasMany(x => x.Attachments)
            .WithOne(x => x.Message)
            .HasForeignKey(x => x.MessageId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
```
::CONFIG

### CONFIG::RequestMessageAttachmentConfiguration
FILE: src/Infrastructure/Data/Configurations/RequestMessageAttachmentConfiguration.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using YourApp.Domain.Entities;

namespace YourApp.Infrastructure.Data.Configurations;

public class RequestMessageAttachmentConfiguration : IEntityTypeConfiguration<RequestMessageAttachment>
{
    public void Configure(EntityTypeBuilder<RequestMessageAttachment> builder)
    {
        builder.ToTable("RequestMessageAttachments");
        
        builder.HasKey(x => x.Id);
        
        builder.Property(x => x.MessageId)
            .IsRequired();
        
        builder.Property(x => x.PhotoUrl)
            .IsRequired()
            .HasMaxLength(2048);
        
        builder.Property(x => x.OriginalFileName)
            .IsRequired()
            .HasMaxLength(256);
        
        builder.Property(x => x.FileSizeBytes)
            .IsRequired();
        
        builder.Property(x => x.UploadedAt)
            .IsRequired()
            .HasDefaultValueSql("now()");
        
        builder.HasIndex(x => x.MessageId);
        
        // Relationships
        builder.HasOne(x => x.Message)
            .WithMany(x => x.Attachments)
            .HasForeignKey(x => x.MessageId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
```
::CONFIG

---

## API_ENDPOINTS

### ENDPOINT::POST_/api/v1/borrow-requests
REQUEST:
```json
{
  "toolId": "123e4567-e89b-12d3-a456-426614174000",
  "requestedStartDate": "2026-03-15",
  "requestedEndDate": "2026-03-17",
  "intendedUse": "Building a deck in my backyard",
  "pickupTimePreference": "morning",
  "specialRequests": "Need extension cord too if available"
}
```

RESPONSE_201:
```json
{
  "id": "987fcdeb-51a2-43d1-9f2e-123456789abc",
  "toolId": "123e4567-e89b-12d3-a456-426614174000",
  "toolTitle": "DeWalt Circular Saw",
  "borrowerId": "456e7890-e12b-34c5-d678-901234567890",
  "borrowerName": "John Smith",
  "requestedStartDate": "2026-03-15",
  "requestedEndDate": "2026-03-17",
  "intendedUse": "Building a deck in my backyard",
  "pickupTimePreference": "morning",
  "specialRequests": "Need extension cord too if available",
  "status": "pending",
  "createdAt": "2026-02-16T10:30:00Z",
  "expiresAt": "2026-02-18T10:30:00Z"
}
```

RESPONSE_400:
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "Validation failed",
  "status": 400,
  "errors": {
    "RequestedStartDate": ["Start date must be in the future"],
    "IntendedUse": ["Intended use is required and must be 50-500 characters"]
  }
}
```

RESPONSE_409:
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.8",
  "title": "Tool unavailable",
  "status": 409,
  "detail": "Tool is unavailable for the requested dates",
  "conflictingDates": ["2026-03-15", "2026-03-16", "2026-03-17"]
}
```

CONTROLLER:
FILE: src/API/Controllers/BorrowRequestsController.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using YourApp.Application.DTOs.BorrowRequests;
using YourApp.Application.Services;
using YourApp.Domain.Exceptions;

namespace YourApp.API.Controllers;

[ApiController]
[Route("api/v1/borrow-requests")]
[Authorize]
public class BorrowRequestsController : ControllerBase
{
    private readonly IBorrowRequestService _borrowRequestService;
    
    public BorrowRequestsController(IBorrowRequestService borrowRequestService)
    {
        