# Project Context for Claude Code

## What This Repository Is

This is a **forked instance** of the Agentic Development Framework. The repository contains:

1. **Specifications** (in `docs/`) - Agent-generated planning documents
2. **Implementation** (in `src/`) - Code that implements those specifications
3. **State machine** (in `docs/.state/`) - Orchestration metadata

You are being invoked to **implement features based on engineering specifications**.

## Your Role

You are an **implementation agent**. Your job:

1. Read the engineering specification for a feature
2. Generate production-quality code that implements that spec
3. Follow the tech stack standards defined in the project
4. Create tests with appropriate coverage
5. Commit your changes to the current feature branch

You are **not** creating the specifications. Those already exist in `docs/04-specs/`.

## How You're Invoked

When the orchestrator calls you, it will:

1. Check out a feature branch (e.g., `feature/book-selection-impl`)
2. Place the relevant engineering spec at `IMPLEMENTATION_SPEC.md` in the branch
3. Ask you to implement it

Your workflow:
```bash
# The spec is in the branch
cat IMPLEMENTATION_SPEC.md

# Implement according to the spec
# Generate code in src/
# Generate tests in tests/

# Commit as you go
git add .
git commit -m "feat: implement [component]"
```

## Tech Stack (Read This First)

The project tech stack is defined in `context/tech-stack-standards.md`. **You must follow these standards.**

Key constraints (refer to full doc for details):
- **Backend**: ASP.NET Core 8, C# 12, EF Core 8, PostgreSQL
- **Frontend**: React 18, TypeScript, Vite, TanStack Query, Tailwind CSS
- **Testing**: xUnit, FluentAssertions, Vitest, Playwright
- **Patterns**: Code-first migrations, policy-based auth, nullable reference types enabled

**Read `context/tech-stack-standards.md` before implementing anything.**

## Implementation Checklist

When implementing a feature, ensure:

### Database Layer
- [ ] Entity classes with proper EF Core configuration
- [ ] Migration file (code-first)
- [ ] Indexes defined for performance
- [ ] Foreign keys and cascade rules correct

### API Layer
- [ ] Controllers with proper routing (`/api/v1/...`)
- [ ] Request/response DTOs with validation (FluentValidation)
- [ ] Authorization policies applied (`[Authorize(Policy = "...")]`)
- [ ] Error responses use ProblemDetails (RFC 7807)
- [ ] All endpoints documented in code comments

### Service Layer
- [ ] Interfaces in `Application/` 
- [ ] Implementations in `Infrastructure/`
- [ ] Async/await throughout (no `.Result` or `.Wait()`)
- [ ] Proper error handling and logging

### Frontend Layer
- [ ] React components with TypeScript
- [ ] TanStack Query hooks for server state
- [ ] Tailwind for styling (utility classes only)
- [ ] Forms validated client-side
- [ ] Error states handled gracefully

### Testing
- [ ] Unit tests for business logic (>70% coverage)
- [ ] Integration tests for API endpoints
- [ ] Tests follow naming: `MethodName_Scenario_ExpectedResult`
- [ ] Use FluentAssertions for readable assertions

## File Organization

Follow this structure (already set up in template):

```
src/
├── API/
│   ├── Controllers/
│   ├── Middleware/
│   └── Program.cs
├── Application/
│   ├── Services/
│   ├── Interfaces/
│   └── DTOs/
├── Domain/
│   ├── Entities/
│   └── ValueObjects/
└── Infrastructure/
    ├── Data/
    │   ├── ApplicationDbContext.cs
    │   ├── Configurations/
    │   └── Migrations/
    └── Services/

tests/
├── Unit/
│   └── [Feature]Tests.cs
├── Integration/
│   └── [Feature]IntegrationTests.cs
└── E2E/
    └── [Feature].spec.ts
```

## What the Spec Contains

The engineering spec (`IMPLEMENTATION_SPEC.md`) will include:

1. **Data Model** - Entities, properties, relationships
2. **Database Schema** - Migration code (you'll adapt this to EF Core)
3. **API Endpoints** - Routes, methods, request/response formats
4. **Service Layer** - Interfaces and business logic
5. **Frontend Components** - Component structure and behavior
6. **Testing Strategy** - What to test and how

**Implement exactly what the spec describes.** If the spec is ambiguous, note it in comments and implement the most reasonable interpretation.

## Coding Standards

### C# (.NET)

```csharp
// ✅ Good
public class BookSuggestion
{
    public Guid Id { get; init; }
    public string Title { get; init; } = null!;
    public DateTime CreatedAt { get; init; }
}

// ❌ Bad
public class BookSuggestion
{
    public Guid Id { get; set; }  // Use init for immutability
    public string Title { get; set; }  // Missing null-forgiving operator
    public DateTime CreatedAt;  // Use properties, not fields
}
```

- Nullable reference types enabled
- Use `init` for immutable properties
- Records for DTOs
- Async all the way down

### TypeScript (React)

```typescript
// ✅ Good
interface BookSuggestion {
  id: string;
  title: string;
  voteCount: number;
}

export function SuggestionCard({ suggestion }: { suggestion: BookSuggestion }) {
  return <div className="p-4 border rounded">{suggestion.title}</div>;
}

// ❌ Bad
export function SuggestionCard(props: any) {  // No any types
  return <div style={{ padding: 4 }}>{props.title}</div>;  // Use Tailwind, not inline styles
}
```

- Strict TypeScript (no `any`)
- Props interfaces defined
- Tailwind for styling (no CSS-in-JS)
- Functional components only

### Testing

```csharp
// ✅ Good
[Fact]
public async Task CreateSuggestion_ValidData_ReturnsCreated()
{
    // Arrange
    var request = new CreateSuggestionRequest { Title = "Test" };
    
    // Act
    var result = await _service.CreateSuggestionAsync(request);
    
    // Assert
    result.Should().NotBeNull();
    result.Title.Should().Be("Test");
}

// ❌ Bad
[Fact]
public void Test1()  // Meaningless name
{
    var result = _service.CreateSuggestion(null).Result;  // Sync over async, null input
    Assert.True(result != null);  // Weak assertion
}
```

## Common Patterns

### Entity Configuration (EF Core)

```csharp
public class BookSuggestionConfiguration : IEntityTypeConfiguration<BookSuggestion>
{
    public void Configure(EntityTypeBuilder<BookSuggestion> builder)
    {
        builder.ToTable("BookSuggestions");
        
        builder.HasKey(x => x.Id);
        
        builder.Property(x => x.Title)
            .IsRequired()
            .HasMaxLength(500);
        
        builder.HasIndex(x => x.GroupId);
    }
}
```

### API Controller

```csharp
[ApiController]
[Route("api/v1/[controller]")]
[Authorize]
public class SuggestionsController : ControllerBase
{
    private readonly ISuggestionService _service;
    
    [HttpPost]
    [ProducesResponseType(typeof(SuggestionDto), 201)]
    [ProducesResponseType(typeof(ProblemDetails), 400)]
    public async Task<ActionResult<SuggestionDto>> Create(
        [FromBody] CreateSuggestionRequest request)
    {
        var result = await _service.CreateAsync(request);
        return CreatedAtAction(nameof(GetById), new { id = result.Id }, result);
    }
}
```

### React Component with Query

```typescript
export function SuggestionList({ groupId }: { groupId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['suggestions', groupId],
    queryFn: () => api.getSuggestions(groupId),
  });
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading suggestions</div>;
  
  return (
    <div className="space-y-4">
      {data?.suggestions.map(s => (
        <SuggestionCard key={s.id} suggestion={s} />
      ))}
    </div>
  );
}
```

## What NOT to Do

❌ **Don't** create files not specified in the spec  
❌ **Don't** use technologies not in the tech stack  
❌ **Don't** skip tests ("I'll add them later")  
❌ **Don't** use `any` types in TypeScript  
❌ **Don't** use inline styles (use Tailwind)  
❌ **Don't** create lazy-loaded navigation properties (EF Core)  
❌ **Don't** use `.Result` or `.Wait()` (async all the way)  
❌ **Don't** hardcode configuration (use appsettings.json)  
❌ **Don't** skip input validation  
❌ **Don't** forget authorization checks

## Commit Strategy

Make **atomic commits** as you implement:

```bash
git commit -m "feat(data): add BookSuggestion entity and configuration"
git commit -m "feat(data): add CreateBookSuggestions migration"
git commit -m "feat(api): add SuggestionsController with CRUD endpoints"
git commit -m "feat(services): implement BookSuggestionService"
git commit -m "test(services): add BookSuggestionService unit tests"
git commit -m "feat(ui): add SuggestionList and SuggestionCard components"
git commit -m "test(ui): add SuggestionCard component tests"
```

Use conventional commits:
- `feat`: New feature
- `fix`: Bug fix
- `test`: Adding tests
- `refactor`: Code refactoring
- `docs`: Documentation
- `chore`: Maintenance

## When You're Done

After implementing the spec:

1. Run tests: `dotnet test && npm test`
2. Check coverage: Ensure >70%
3. Run linters: `dotnet format && npm run lint`
4. Verify the app runs: `dotnet run` and check localhost

The CI pipeline will validate:
- All tests pass
- Coverage threshold met
- No linting errors
- No security vulnerabilities

If CI passes, the PR will be ready for human review.

## If the Spec is Unclear

If you encounter ambiguity in the spec:

1. Implement the most reasonable interpretation
2. Add a `// TODO: Clarify with product` comment
3. Note it in the PR description
4. Continue implementing

Don't block on ambiguity—implement what makes sense and flag for review.

## Integration Points

Your implementation will integrate with:

- **Foundation code** (if building a feature)
  - Use existing entities from `Domain/Entities`
  - Use existing services from `Application/Services`
  - Follow existing patterns

- **Other features** (if dependencies exist)
  - Check other feature specs in `docs/04-specs/`
  - Ensure API contracts align
  - Share DTOs where appropriate

## Example: Implementing a Feature

```bash
# You're invoked on feature/book-selection-impl branch

# 1. Read the spec
cat IMPLEMENTATION_SPEC.md

# 2. Check tech stack standards
cat context/tech-stack-standards.md

# 3. Implement in order:
#    a. Data layer (entities, configurations, migrations)
#    b. Service layer (interfaces, implementations)
#    c. API layer (controllers, DTOs, validation)
#    d. Frontend (components, hooks, pages)
#    e. Tests (unit, integration, e2e)

# 4. Commit atomically as you go

# 5. Final checks
dotnet test
npm test
dotnet format --verify-no-changes
npm run lint

# 6. Push
git push origin feature/book-selection-impl

# The orchestrator will create a PR for human review
```

## Key Principle

**You are implementing a specification that was carefully refined through multiple agent iterations.**

The spec is the source of truth. Implement it faithfully. If you think the spec has a problem, note it for human review, but still implement what it says.

Your job is **execution**, not **design**. The design is done. Now build it.

---

## Quick Reference

- **Tech Stack**: `context/tech-stack-standards.md`
- **Spec to Implement**: `IMPLEMENTATION_SPEC.md` (in your branch)
- **Foundation Spec**: `docs/05-specs/foundation-spec.md`
- **Other Features**: `docs/05-specs/*.md`
- **State Machine**: Don't touch `docs/.state/` (orchestrator manages)

**Questions?** Add comments in code and flag in PR. Don't guess—implement what makes sense and let humans decide.
