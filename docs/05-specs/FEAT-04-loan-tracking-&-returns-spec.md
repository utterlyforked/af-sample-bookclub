# Loan Tracking & Returns - Implementation Specification

META::
  type: feature
  component: loan-tracking-returns
  dependencies: user-auth, borrowing-request-system, photo-service, email-service, background-jobs
  tech_stack: ASP.NET Core 8, React 18, PostgreSQL 16
  estimated_effort_hours: 35
::META

---

## IMPLEMENTATION_ORDER

STEP_1: Database schema and migrations for Loan entities
STEP_2: Domain entities and EF Core configurations
STEP_3: Loan state machine service implementation
STEP_4: Background job services for reminders and status transitions
STEP_5: API controllers for loan management
STEP_6: DTOs and validation for loan operations
STEP_7: Frontend API client for loan operations
STEP_8: Frontend dashboard and loan management components
STEP_9: Unit tests for loan services and state machine
STEP_10: Integration tests for loan workflows

---

## DATABASE_SCHEMA

### TABLE::Loans
```sql
CREATE TABLE "Loans" (
    "Id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "BorrowRequestId" uuid NOT NULL,
    "OwnerId" uuid NOT NULL,
    "BorrowerId" uuid NOT NULL,
    "ToolId" uuid NOT NULL,
    "Status" varchar(50) NOT NULL,
    "PickupDate" timestamp with time zone NOT NULL,
    "ExpectedReturnDate" timestamp with time zone NOT NULL,
    "ActualReturnDate" timestamp with time zone NULL,
    "ReturnLocationAddress" varchar(500) NOT NULL,
    "SpecialInstructions" text NULL,
    "BorrowerReturnMarkedAt" timestamp with time zone NULL,
    "OwnerConfirmedReturnAt" timestamp with time zone NULL,
    "OwnerConfirmationDueDate" timestamp with time zone NULL,
    "CreatedAt" timestamp with time zone NOT NULL DEFAULT now(),
    "UpdatedAt" timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX "IX_Loans_OwnerId" ON "Loans"("OwnerId");
CREATE INDEX "IX_Loans_BorrowerId" ON "Loans"("BorrowerId");
CREATE INDEX "IX_Loans_Status" ON "Loans"("Status");
CREATE INDEX "IX_Loans_ExpectedReturnDate" ON "Loans"("ExpectedReturnDate");
CREATE INDEX "IX_Loans_Status_ExpectedReturnDate" ON "Loans"("Status", "ExpectedReturnDate");

ALTER TABLE "Loans" ADD CONSTRAINT "FK_Loans_Users_OwnerId" 
    FOREIGN KEY ("OwnerId") REFERENCES "Users"("Id") ON DELETE RESTRICT;
ALTER TABLE "Loans" ADD CONSTRAINT "FK_Loans_Users_BorrowerId" 
    FOREIGN KEY ("BorrowerId") REFERENCES "Users"("Id") ON DELETE RESTRICT;
ALTER TABLE "Loans" ADD CONSTRAINT "FK_Loans_Tools_ToolId" 
    FOREIGN KEY ("ToolId") REFERENCES "Tools"("Id") ON DELETE RESTRICT;
ALTER TABLE "Loans" ADD CONSTRAINT "FK_Loans_BorrowRequests_BorrowRequestId" 
    FOREIGN KEY ("BorrowRequestId") REFERENCES "BorrowRequests"("Id") ON DELETE RESTRICT;
```
::TABLE

### TABLE::LoanPhotos
```sql
CREATE TABLE "LoanPhotos" (
    "Id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "LoanId" uuid NOT NULL,
    "PhotoUrl" varchar(2048) NOT NULL,
    "PhotoType" varchar(50) NOT NULL,
    "PhotoOrder" int NOT NULL,
    "UploadedAt" timestamp with time zone NOT NULL DEFAULT now(),
    "IsDeleted" boolean NOT NULL DEFAULT false
);

CREATE INDEX "IX_LoanPhotos_LoanId" ON "LoanPhotos"("LoanId");
CREATE INDEX "IX_LoanPhotos_LoanId_PhotoType" ON "LoanPhotos"("LoanId", "PhotoType");

ALTER TABLE "LoanPhotos" ADD CONSTRAINT "FK_LoanPhotos_Loans_LoanId" 
    FOREIGN KEY ("LoanId") REFERENCES "Loans"("Id") ON DELETE CASCADE;
    
ALTER TABLE "LoanPhotos" ADD CONSTRAINT "CK_LoanPhotos_PhotoOrder" 
    CHECK ("PhotoOrder" BETWEEN 1 AND 3);
ALTER TABLE "LoanPhotos" ADD CONSTRAINT "CK_LoanPhotos_PhotoType" 
    CHECK ("PhotoType" IN ('pickup_condition', 'return_condition'));
```
::TABLE

### TABLE::LoanStatusHistory
```sql
CREATE TABLE "LoanStatusHistory" (
    "Id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "LoanId" uuid NOT NULL,
    "PreviousStatus" varchar(50) NULL,
    "NewStatus" varchar(50) NOT NULL,
    "ChangedAt" timestamp with time zone NOT NULL DEFAULT now(),
    "ChangedByUserId" uuid NULL,
    "Notes" text NULL,
    "IsSystemGenerated" boolean NOT NULL DEFAULT false
);

CREATE INDEX "IX_LoanStatusHistory_LoanId" ON "LoanStatusHistory"("LoanId");
CREATE INDEX "IX_LoanStatusHistory_ChangedAt" ON "LoanStatusHistory"("ChangedAt");

ALTER TABLE "LoanStatusHistory" ADD CONSTRAINT "FK_LoanStatusHistory_Loans_LoanId" 
    FOREIGN KEY ("LoanId") REFERENCES "Loans"("Id") ON DELETE CASCADE;
ALTER TABLE "LoanStatusHistory" ADD CONSTRAINT "FK_LoanStatusHistory_Users_ChangedByUserId" 
    FOREIGN KEY ("ChangedByUserId") REFERENCES "Users"("Id") ON DELETE SET NULL;
```
::TABLE

### TABLE::LoanExtensions
```sql
CREATE TABLE "LoanExtensions" (
    "Id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "LoanId" uuid NOT NULL,
    "RequestedAt" timestamp with time zone NOT NULL DEFAULT now(),
    "RequestedByUserId" uuid NOT NULL,
    "OldReturnDate" timestamp with time zone NOT NULL,
    "NewReturnDate" timestamp with time zone NOT NULL,
    "Reason" text NOT NULL,
    "Status" varchar(50) NOT NULL DEFAULT 'pending',
    "RespondedAt" timestamp with time zone NULL,
    "RespondedByUserId" uuid NULL,
    "ResponseMessage" text NULL
);

CREATE INDEX "IX_LoanExtensions_LoanId" ON "LoanExtensions"("LoanId");
CREATE INDEX "IX_LoanExtensions_Status" ON "LoanExtensions"("Status");

ALTER TABLE "LoanExtensions" ADD CONSTRAINT "FK_LoanExtensions_Loans_LoanId" 
    FOREIGN KEY ("LoanId") REFERENCES "Loans"("Id") ON DELETE CASCADE;
ALTER TABLE "LoanExtensions" ADD CONSTRAINT "FK_LoanExtensions_Users_RequestedByUserId" 
    FOREIGN KEY ("RequestedByUserId") REFERENCES "Users"("Id") ON DELETE RESTRICT;
ALTER TABLE "LoanExtensions" ADD CONSTRAINT "FK_LoanExtensions_Users_RespondedByUserId" 
    FOREIGN KEY ("RespondedByUserId") REFERENCES "Users"("Id") ON DELETE RESTRICT;
    
ALTER TABLE "LoanExtensions" ADD CONSTRAINT "CK_LoanExtensions_Status" 
    CHECK ("Status" IN ('pending', 'approved', 'denied'));
```
::TABLE

### TABLE::LoanReminders
```sql
CREATE TABLE "LoanReminders" (
    "Id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "LoanId" uuid NOT NULL,
    "ReminderType" varchar(50) NOT NULL,
    "ScheduledAt" timestamp with time zone NOT NULL,
    "SentAt" timestamp with time zone NULL,
    "EmailDelivered" boolean NULL,
    "DeliveryAttempts" int NOT NULL DEFAULT 0,
    "LastDeliveryError" text NULL,
    "CreatedAt" timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX "IX_LoanReminders_LoanId" ON "LoanReminders"("LoanId");
CREATE INDEX "IX_LoanReminders_ScheduledAt_SentAt" ON "LoanReminders"("ScheduledAt", "SentAt");
CREATE INDEX "IX_LoanReminders_ReminderType" ON "LoanReminders"("ReminderType");

ALTER TABLE "LoanReminders" ADD CONSTRAINT "FK_LoanReminders_Loans_LoanId" 
    FOREIGN KEY ("LoanId") REFERENCES "Loans"("Id") ON DELETE CASCADE;
    
ALTER TABLE "LoanReminders" ADD CONSTRAINT "CK_LoanReminders_ReminderType" 
    CHECK ("ReminderType" IN ('48_hour', '24_hour', 'day_of', 'overdue_day1', 'overdue_day3'));
```
::TABLE

### MIGRATION::20260216_CreateLoans
```csharp
public partial class CreateLoans : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        // COPY THIS EXACTLY
        migrationBuilder.CreateTable(
            name: "Loans",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                BorrowRequestId = table.Column<Guid>(type: "uuid", nullable: false),
                OwnerId = table.Column<Guid>(type: "uuid", nullable: false),
                BorrowerId = table.Column<Guid>(type: "uuid", nullable: false),
                ToolId = table.Column<Guid>(type: "uuid", nullable: false),
                Status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                PickupDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                ExpectedReturnDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                ActualReturnDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                ReturnLocationAddress = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                SpecialInstructions = table.Column<string>(type: "text", nullable: true),
                BorrowerReturnMarkedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                OwnerConfirmedReturnAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                OwnerConfirmationDueDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()"),
                UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()")
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_Loans", x => x.Id);
                table.ForeignKey(
                    name: "FK_Loans_BorrowRequests_BorrowRequestId",
                    column: x => x.BorrowRequestId,
                    principalTable: "BorrowRequests",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Restrict);
                table.ForeignKey(
                    name: "FK_Loans_Tools_ToolId",
                    column: x => x.ToolId,
                    principalTable: "Tools",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Restrict);
                table.ForeignKey(
                    name: "FK_Loans_Users_BorrowerId",
                    column: x => x.BorrowerId,
                    principalTable: "Users",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Restrict);
                table.ForeignKey(
                    name: "FK_Loans_Users_OwnerId",
                    column: x => x.OwnerId,
                    principalTable: "Users",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Restrict);
            });

        migrationBuilder.CreateTable(
            name: "LoanPhotos",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                LoanId = table.Column<Guid>(type: "uuid", nullable: false),
                PhotoUrl = table.Column<string>(type: "character varying(2048)", maxLength: 2048, nullable: false),
                PhotoType = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                PhotoOrder = table.Column<int>(type: "integer", nullable: false),
                UploadedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()"),
                IsDeleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_LoanPhotos", x => x.Id);
                table.ForeignKey(
                    name: "FK_LoanPhotos_Loans_LoanId",
                    column: x => x.LoanId,
                    principalTable: "Loans",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
                table.CheckConstraint("CK_LoanPhotos_PhotoOrder", "\"PhotoOrder\" BETWEEN 1 AND 3");
                table.CheckConstraint("CK_LoanPhotos_PhotoType", "\"PhotoType\" IN ('pickup_condition', 'return_condition')");
            });

        migrationBuilder.CreateTable(
            name: "LoanStatusHistory",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                LoanId = table.Column<Guid>(type: "uuid", nullable: false),
                PreviousStatus = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                NewStatus = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                ChangedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()"),
                ChangedByUserId = table.Column<Guid>(type: "uuid", nullable: true),
                Notes = table.Column<string>(type: "text", nullable: true),
                IsSystemGenerated = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_LoanStatusHistory", x => x.Id);
                table.ForeignKey(
                    name: "FK_LoanStatusHistory_Loans_LoanId",
                    column: x => x.LoanId,
                    principalTable: "Loans",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
                table.ForeignKey(
                    name: "FK_LoanStatusHistory_Users_ChangedByUserId",
                    column: x => x.ChangedByUserId,
                    principalTable: "Users",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.SetNull);
            });

        migrationBuilder.CreateTable(
            name: "LoanExtensions",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                LoanId = table.Column<Guid>(type: "uuid", nullable: false),
                RequestedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()"),
                RequestedByUserId = table.Column<Guid>(type: "uuid", nullable: false),
                OldReturnDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                NewReturnDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                Reason = table.Column<string>(type: "text", nullable: false),
                Status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValue: "pending"),
                RespondedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                RespondedByUserId = table.Column<Guid>(type: "uuid", nullable: true),
                ResponseMessage = table.Column<string>(type: "text", nullable: true)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_LoanExtensions", x => x.Id);
                table.ForeignKey(
                    name: "FK_LoanExtensions_Loans_LoanId",
                    column: x => x.LoanId,
                    principalTable: "Loans",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
                table.ForeignKey(
                    name: "FK_LoanExtensions_Users_RequestedByUserId",
                    column: x => x.RequestedByUserId,
                    principalTable: "Users",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Restrict);
                table.ForeignKey(
                    name: "FK_LoanExtensions_Users_RespondedByUserId",
                    column: x => x.RespondedByUserId,
                    principalTable: "Users",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Restrict);
                table.CheckConstraint("CK_LoanExtensions_Status", "\"Status\" IN ('pending', 'approved', 'denied')");
            });

        migrationBuilder.CreateTable(
            name: "LoanReminders",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                LoanId = table.Column<Guid>(type: "uuid", nullable: false),
                ReminderType = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                ScheduledAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                SentAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                EmailDelivered = table.Column<bool>(type: "boolean", nullable: true),
                DeliveryAttempts = table.Column<int>(type: "integer", nullable: false, defaultValue: 0),
                LastDeliveryError = table.Column<string>(type: "text", nullable: true),
                CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false, defaultValueSql: "now()")
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_LoanReminders", x => x.Id);
                table.ForeignKey(
                    name: "FK_LoanReminders_Loans_LoanId",
                    column: x => x.LoanId,
                    principalTable: "Loans",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Cascade);
                table.CheckConstraint("CK_LoanReminders_ReminderType", "\"ReminderType\" IN ('48_hour', '24_hour', 'day_of', 'overdue_day1', 'overdue_day3')");
            });

        migrationBuilder.CreateIndex(
            name: "IX_Loans_BorrowerId",
            table: "Loans",
            column: "BorrowerId");

        migrationBuilder.CreateIndex(
            name: "IX_Loans_ExpectedReturnDate",
            table: "Loans",
            column: "ExpectedReturnDate");

        migrationBuilder.CreateIndex(
            name: "IX_Loans_OwnerId",
            table: "Loans",
            column: "OwnerId");

        migrationBuilder.CreateIndex(
            name: "IX_Loans_Status",
            table: "Loans",
            column: "Status");

        migrationBuilder.CreateIndex(
            name: "IX_Loans_Status_ExpectedReturnDate",
            table: "Loans",
            columns: new[] { "Status", "ExpectedReturnDate" });

        migrationBuilder.CreateIndex(
            name: "IX_LoanExtensions_LoanId",
            table: "LoanExtensions",
            column: "LoanId");

        migrationBuilder.CreateIndex(
            name: "IX_LoanExtensions_Status",
            table: "LoanExtensions",
            column: "Status");

        migrationBuilder.CreateIndex(
            name: "IX_LoanPhotos_LoanId",
            table: "LoanPhotos",
            column: "LoanId");

        migrationBuilder.CreateIndex(
            name: "IX_LoanPhotos_LoanId_PhotoType",
            table: "LoanPhotos",
            columns: new[] { "LoanId", "PhotoType" });

        migrationBuilder.CreateIndex(
            name: "IX_LoanReminders_LoanId",
            table: "LoanReminders",
            column: "LoanId");

        migrationBuilder.CreateIndex(
            name: "IX_LoanReminders_ReminderType",
            table: "LoanReminders",
            column: "ReminderType");

        migrationBuilder.CreateIndex(
            name: "IX_LoanReminders_ScheduledAt_SentAt",
            table: "LoanReminders",
            columns: new[] { "ScheduledAt", "SentAt" });

        migrationBuilder.CreateIndex(
            name: "IX_LoanStatusHistory_ChangedAt",
            table: "LoanStatusHistory",
            column: "ChangedAt");

        migrationBuilder.CreateIndex(
            name: "IX_LoanStatusHistory_LoanId",
            table: "LoanStatusHistory",
            column: "LoanId");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "LoanExtensions");
        migrationBuilder.DropTable(name: "LoanPhotos");
        migrationBuilder.DropTable(name: "LoanReminders");
        migrationBuilder.DropTable(name: "LoanStatusHistory");
        migrationBuilder.DropTable(name: "Loans");
    }
}
```
::MIGRATION

---

## DOMAIN_ENTITIES

### ENTITY::Loan
FILE: src/Domain/Entities/Loan.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
using System;

namespace ToolShare.Domain.Entities;

public class Loan
{
    public Guid Id { get; init; }
    public Guid BorrowRequestId { get; init; }
    public Guid OwnerId { get; init; }
    public Guid BorrowerId { get; init; }
    public Guid ToolId { get; init; }
    public LoanStatus Status { get; set; }
    public DateTime PickupDate { get; init; }
    public DateTime ExpectedReturnDate { get; set; }
    public DateTime? ActualReturnDate { get; set; }
    public string ReturnLocationAddress { get; init; } = null!;
    public string? SpecialInstructions { get; init; }
    public DateTime? BorrowerReturnMarkedAt { get; set; }
    public DateTime? OwnerConfirmedReturnAt { get; set; }
    public DateTime? OwnerConfirmationDueDate { get; set; }
    public DateTime CreatedAt { get; init; }
    public DateTime UpdatedAt { get; set; }
    
    // Navigation properties
    public User Owner { get; init; } = null!;
    public User Borrower { get; init; } = null!;
    public Tool Tool { get; init; } = null!;
    public BorrowRequest BorrowRequest { get; init; } = null!;
    public ICollection<LoanPhoto> Photos { get; init; } = new List<LoanPhoto>();
    public ICollection<LoanStatusHistory> StatusHistory { get; init; } = new List<LoanStatusHistory>();
    public ICollection<LoanExtension> Extensions { get; init; } = new List<LoanExtension>();
    public ICollection<LoanReminder> Reminders { get; init; } = new List<LoanReminder>();
    
    // Helper methods
    public bool IsOverdue => DateTime.UtcNow > ExpectedReturnDate && Status != LoanStatus.Completed && Status != LoanStatus.Lost;
    public int DaysUntilDue => (ExpectedReturnDate.Date - DateTime.UtcNow.Date).Days;
    public bool RequiresOwnerConfirmation => Status == LoanStatus.ReturnPending && OwnerConfirmationDueDate > DateTime.UtcNow;
}

public enum LoanStatus
{
    Active,
    DueSoon,
    Overdue,
    ReturnPending,
    ReturnDisputed,
    Completed,
    Lost
}
```
::ENTITY

### ENTITY::LoanPhoto
FILE: src/Domain/Entities/LoanPhoto.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
using System;

namespace ToolShare.Domain.Entities;

public class LoanPhoto
{
    public Guid Id { get; init; }
    public Guid LoanId { get; init; }
    public string PhotoUrl { get; init; } = null!;
    public LoanPhotoType PhotoType { get; init; }
    public int PhotoOrder { get; init; }
    public DateTime UploadedAt { get; init; }
    public bool IsDeleted { get; set; }
    
    // Navigation properties
    public Loan Loan { get; init; } = null!;
}

public enum LoanPhotoType
{
    PickupCondition,
    ReturnCondition
}
```
::ENTITY

### ENTITY::LoanStatusHistory
FILE: src/Domain/Entities/LoanStatusHistory.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
using System;

namespace ToolShare.Domain.Entities;

public class LoanStatusHistory
{
    public Guid Id { get; init; }
    public Guid LoanId { get; init; }
    public LoanStatus? PreviousStatus { get; init; }
    public LoanStatus NewStatus { get; init; }
    public DateTime ChangedAt { get; init; }
    public Guid? ChangedByUserId { get; init; }
    public string? Notes { get; init; }
    public bool IsSystemGenerated { get; init; }
    
    // Navigation properties
    public Loan Loan { get; init; } = null!;
    public User? ChangedBy { get; init; }
}
```
::ENTITY

### ENTITY::LoanExtension
FILE: src/Domain/Entities/LoanExtension.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
using System;

namespace ToolShare.Domain.Entities;

public class LoanExtension
{
    public Guid Id { get; init; }
    public Guid LoanId { get; init; }
    public DateTime RequestedAt { get; init; }
    public Guid RequestedByUserId { get; init; }
    public DateTime OldReturnDate { get; init; }
    public DateTime NewReturnDate { get; init; }
    public string Reason { get; init; } = null!;
    public ExtensionStatus Status { get; set; }
    public DateTime? RespondedAt { get; set; }
    public Guid? RespondedByUserId { get; set; }
    public string? ResponseMessage { get; set; }
    
    // Navigation properties
    public Loan Loan { get; init; } = null!;
    public User RequestedBy { get; init; } = null!;
    public User? RespondedBy { get; init; }
}

public enum ExtensionStatus
{
    Pending,
    Approved,
    Denied
}
```
::ENTITY

### ENTITY::LoanReminder
FILE: src/Domain/Entities/LoanReminder.cs
```csharp
// COPY THIS EXACTLY - DO NOT MODIFY
using System;

namespace ToolShare.Domain.Entities;

public class LoanReminder
{
    public Guid Id { get; init; }
    public Guid LoanId { get; init; }
    public ReminderType ReminderType { get; init; }
    public DateTime ScheduledAt { get; init; }
    public DateTime? SentAt { get; set; }
    public bool? EmailDelivered { get; set; }
    public int DeliveryAttempts { get; set; }
    public string? LastDeliveryError { get; set; }
    public DateTime CreatedAt { get; init; }
    
    // Navigation properties
    public Loan Loan { get; init; } = null!;
}

public enum ReminderType
{
    FortyEightHour,
    TwentyFourHour,
    DayOf,
    OverdueDay1,
    OverdueDay3
}
```
::ENTITY

---

## EF_CORE_CONFIGURATIONS

### CONFIG::LoanConfiguration
FILE: src/Infrastructure/Data/Configurations/LoanConfiguration.cs
```csharp
// COPY THIS EXACTLY
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using ToolShare.Domain.Entities;

namespace ToolShare.Infrastructure.Data.Configurations;

public class LoanConfiguration : IEntityTypeConfiguration<Loan>
{
    public void Configure(EntityTypeBuilder<Loan> builder)
    {
        builder.ToTable("Loans");
        
        builder.HasKey(x => x.Id);
        
        builder.Property(x => x.Status)
            .IsRequired()
            .HasMaxLength(50)
            .HasConversion<string>();
        
        builder.Property(x => x.ReturnLocationAddress)
            .IsRequired()
            .HasMaxLength(500);
        
        builder.Property(x => x.CreatedAt)
            .IsRequired()
            .HasDefaultValueSql("now()");
        
        builder.Property(x => x.UpdatedAt)
            .IsRequired()
            .HasDefaultValueSql("now()");
        
        // Relationships
        builder.HasOne(x => x.Owner)
            .WithMany()
            .HasForeignKey(x => x.OwnerId)
            .OnDelete(DeleteBehavior.Restrict);
        
        builder.HasOne(x => x.Borrower)
            .WithMany()
            .HasForeignKey(x => x.BorrowerId)
            .OnDelete(DeleteBehavior.Restrict);
        
        builder.HasOne(x => x.Tool)
            .WithMany()
            .HasForeignKey(x => x.ToolId)
            .OnDelete(DeleteBehavior.Restrict);
        
        builder.HasOne(x => x.BorrowRequest)
            .WithMany()
            .HasForeignKey(x => x.BorrowRequestId)
            .OnDelete(DeleteBehavior.Restrict);
        
        builder.HasMany(x => x.Photos)
            .WithOne(x => x.Loan)
            .HasForeignKey(x => x.LoanId)
            .OnDelete(DeleteBehavior.Cascade);
        
        builder.HasMany(x => x.StatusHistory)
            .WithOne(x