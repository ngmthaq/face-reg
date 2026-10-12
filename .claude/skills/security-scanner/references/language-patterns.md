# Language & Framework Patterns

Load only the sections that match the stack you found in Step 1. Each section lists:

- **Sources** — where untrusted data comes in.
- **Sinks** — where that data becomes dangerous.
- Common traps for each framework.

---

## JavaScript / TypeScript

**Sources:** `req.body`, `req.query`, `req.params`, `req.headers`, `req.cookies`, `req.files`,
WebSocket messages, `postMessage` events, `location.hash`.

**Sinks:** `child_process.exec`/`execSync`, `eval`, `new Function`, `vm.runInThisContext`,
`innerHTML`, `dangerouslySetInnerHTML`, `fs.readFile`/`sendFile` with a joined path,
`JSON.parse` into a prototype-sensitive merge, raw DB `query()`.

**Express** — `express.json()` with no size limit (DoS). No `helmet()`. `cors({ origin: true })`,
or sending back `Origin` with `credentials: true`. Error middleware that returns `err.stack`.
`app.use(express.static)` on a folder users can write to.

**React** — `dangerouslySetInnerHTML`. `href`/`src` set from user input, which allows `javascript:`.
Secrets in `REACT_APP_*`/`NEXT_PUBLIC_*` (sent to the browser). Tokens in `localStorage`
(XSS can read them, so use `HttpOnly` cookies instead).

**Next.js** — `getServerSideProps` that leaks server-only data into props. API routes with no
auth checks. Middleware matchers that miss protected paths. Server actions that trust
IDs sent by the client.

**Prototype pollution** — recursive `merge`/`extend`/`set` on user JSON that reaches `__proto__`
or `constructor.prototype`. Unsafe versions of `lodash.merge`, `deep-extend`, `query-string` parsers.

**ORM raw-query helpers** — `sequelize.literal`, `knex.raw`, TypeORM
`createQueryBuilder().where("... " + input)`, Prisma `$queryRawUnsafe`.

---

## Python

**Sources:** `request.args`, `request.form`, `request.json`, `request.files`, `request.headers`,
`sys.argv`, environment-driven config.

**Sinks:** `os.system`, `subprocess` with `shell=True`, `eval`/`exec`, `pickle.loads`,
`yaml.load` (without `SafeLoader`), `open()` on a joined path, raw cursor `execute` with
f-strings.

**Django** — `Model.objects.extra()` / `.raw()` with interpolation. `mark_safe` and
`{% autoescape off %}`. `DEBUG = True` in production (leaks settings and stack traces).
`ALLOWED_HOSTS = ["*"]`. `SECRET_KEY` hardcoded in `settings.py`. No
`CsrfViewMiddleware`. Permission checks in views, but not in DRF serializers/viewsets.

**Flask** — `render_template_string` on user input (SSTI → RCE). `app.run(debug=True)`
(Werkzeug console = RCE). `session` signed with a weak `SECRET_KEY`.
`send_file`/`send_from_directory` with an unresolved path.

**FastAPI** — an auth dependency that is not used on every route. Response
models that leak fields (`orm_mode` over a full user record). `Body(...)` that accepts extra
fields into a DB update (mass assignment).

**Requests/urllib** — `verify=False`. User-controlled URLs (SSRF).

---

## Java

**Sources:** `@RequestParam`, `@PathVariable`, `@RequestBody`, `HttpServletRequest`, JMS/Kafka payloads.

**Sinks:** `Runtime.getRuntime().exec`, `ProcessBuilder` with a concatenated command,
`Statement.executeQuery` with `+`, `ObjectInputStream.readObject`, `Class.forName` on user
input, `new File(base + userPath)`.

**Spring Boot** — Actuator endpoints open with no login (`/env`, `/heapdump`).
`@CrossOrigin("*")` with credentials. `permitAll()` patterns that allow more than planned.
No `@PreAuthorize` on service methods that other paths can reach. SpEL evaluation of user
input. `spring.jpa.show-sql` that logs parameters.

**Persistence** — JPQL/HQL string concatenation. `@Query(nativeQuery = true)` with `+`.
MyBatis `${}` (interpolated) instead of `#{}` (bound).

**XML/serialization** — `DocumentBuilderFactory` without
`FEATURE_SECURE_PROCESSING` (XXE). Jackson `enableDefaultTyping`. Log4j `<2.17` (JNDI).

---

## PHP

**Sources:** `$_GET`, `$_POST`, `$_REQUEST`, `$_COOKIE`, `$_FILES`, `$_SERVER['HTTP_*']`.

**Sinks:** `eval`, `system`/`exec`/`shell_exec`/`passthru`/backticks, `include`/`require`
with a variable (LFI/RFI), `unserialize` (object injection), `mysqli_query` with
concatenation, `extract()` on request data, `move_uploaded_file` without extension and MIME
validation.

**Laravel** — `DB::raw` with interpolation. `$fillable`/`$guarded` that allow too much with
`Model::create($request->all())`. `{!! !!}` unescaped Blade output. `APP_DEBUG=true` in
production. Policies that are never called (no `authorize()`).

**General** — loose comparison `==` on hashes or tokens (type juggling, `"0e123" == "0e456"`).
`md5()` for passwords. No `password_verify`.

---

## Go

**Sources:** `r.URL.Query()`, `r.FormValue`, `r.Header`, `mux.Vars(r)`, request bodies.

**Sinks:** `exec.Command("sh", "-c", input)`, `db.Query(fmt.Sprintf(...))`,
`template.HTML(input)` (bypasses `html/template` escaping), `os.Open(filepath.Join(base, input))`
without `filepath.Clean` + prefix check, `http.Get(userURL)` (SSRF).

**Traps** — `text/template` instead of `html/template` for HTML output. Ignored `error`
returns on security-critical calls. `tls.Config{InsecureSkipVerify: true}`. `math/rand`
instead of `crypto/rand` for tokens. No `Server.ReadTimeout` (slowloris). Goroutines that
change shared state without a mutex (race in auth/balance logic).

---

## Ruby

**Sources:** `params`, `request.headers`, `cookies`, uploaded files.

**Sinks:** `eval`, `send`/`public_send` with a user-supplied method name, backticks and
`system`, `Marshal.load`, `YAML.load` (use `safe_load`), `constantize` on user input,
`File.read(params[:path])`.

**Rails** — `where("name = '#{params[:q]}'")` instead of a bound hash or `?` placeholder.
`permit!` or `params.require(:user).permit!` (mass assignment). `html_safe` / `raw` on user
content. `skip_before_action :verify_authenticity_token` on controllers that change data.
Strong-parameter allowlists that include `role` or `admin`. `secret_key_base` committed.

---

## Rust

**Sources:** Axum/Actix extractors (`Query`, `Json`, `Path`), header maps, CLI args.

**Sinks:** `Command::new("sh").arg("-c")`, `sqlx::query()` built via `format!` (use the
compile-time-checked `query!` macro or bind parameters), `unsafe` blocks handling
attacker-controlled lengths or pointers.

**Traps** — `unwrap()`/`expect()` on user input (panic → DoS). Integer math that wraps
in release mode (use `checked_add`/`saturating_*` for money or index math).
`rand::thread_rng` for tokens, where a CSPRNG (`rand::rngs::OsRng`, `ring`) is needed.
`dangerous_configuration()` or turned-off certificate checks in `rustls`/`reqwest`.

---

## .NET / C#

**Sources:** `Request.Query`, `Request.Form`, `[FromBody]`, `Request.Headers`, route values.

**Sinks:** `SqlCommand` with string concatenation (use `SqlParameter`), `Process.Start` with
a composed argument string, `BinaryFormatter` / `JsonConvert` with `TypeNameHandling.All`,
`Path.Combine` with unvalidated user segments, `@Html.Raw`.

**Traps** — no `[ValidateAntiForgeryToken]` on POST actions. `[Authorize]` on the
controller, but `[AllowAnonymous]` left on an action. Over-posting into EF entities (bind to a
separate DTO instead). `ServerCertificateValidationCallback` that returns `true`. Secrets in
`appsettings.json` committed to the repo.
