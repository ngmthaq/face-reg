# Atomic Design

Put every UI component into one of five levels. The level depends on how big the component is and what it is made of.

## Atoms

The smallest parts. You cannot split them more. They work anywhere and you can reuse them everywhere.

```javascript
function Button({ label, variant, onClick, disabled }) {
  return (
    <button className={variant} onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
}
```

## Molecules

Small groups of atoms that work as one unit. Each has one clear job and very little state.

```javascript
function SearchField({ onSearch }) {
  const [query, setQuery] = useState("");
  return (
    <div>
      <Input value={query} onChange={setQuery} />
      <Button label="Search" onClick={() => onSearch(query)} />
    </div>
  );
}
```

## Organisms

Bigger parts of the UI, made of molecules and atoms. They may have business logic or state.

```javascript
function Header({ user, onSearch, onLogout }) {
  return (
    <header>
      <Logo />
      <NavBar items={mainNavItems} />
      <SearchField onSearch={onSearch} />
      <UserMenu user={user} onLogout={onLogout} />
    </header>
  );
}
```

## Templates

Page layouts. They get content through props or slots. They have no real data and do not fetch data.

```javascript
function DashboardTemplate({ sidebar, header, mainContent, footer }) {
  return (
    <div className="dashboard-layout">
      <div className="sidebar">{sidebar}</div>
      <div className="main">
        {header}
        {mainContent}
        {footer}
      </div>
    </div>
  );
}
```

## Pages

Templates filled with real data. Pages make API calls and handle routing and side effects.

```javascript
function DashboardPage() {
  const user = useCurrentUser();
  const stats = useDashboardStats();
  return (
    <DashboardTemplate
      sidebar={<Sidebar user={user} />}
      header={<Header user={user} onSearch={handleSearch} />}
      mainContent={<StatsGrid stats={stats} />}
      footer={<Footer />}
    />
  );
}
```

## Folder Structure

```text
components/
├── atoms/         # Button, Input, Icon, Badge
├── molecules/     # SearchField, FormField, NavItem
├── organisms/     # Header, ProductCard, CommentSection
├── templates/     # DashboardTemplate, AuthTemplate
└── pages/         # HomePage, UserProfilePage
```

## Atomic Design Rules

1. Before you create a component, find its level. Ask: "Is it made of other components? What level are they?"
2. Atoms must never import other components from the same design system.
3. Molecules are made of atoms. Never copy atom code into a molecule.
4. Templates get content through props, slots, or children. They never fetch data or hardcode organisms.
5. Only Pages use routing, data fetching, and global state.
6. Point out wrong levels: "This molecule imports an organism. The levels are upside down."
