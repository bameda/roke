# Playwright (`playwright`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add playwright`.

Browsers for [Playwright](https://playwright.dev/) tests. The box cannot run
them: browsers need many system libraries, and it has no `sudo` to install
them. This service runs them instead, from Playwright's official image,
which has the browsers and everything they need, as a
[Playwright server](https://playwright.dev/docs/docker#remote-connection).

**Inside the box**

| Variable | Value |
|---|---|
| `PW_TEST_CONNECT_WS_ENDPOINT` | `ws://playwright:3000/` |

With it, `npx playwright test` runs the tests in the box and the browsers in
the service, with no change to the project. Do not run
`npx playwright install`: the browsers are already in the service.

**Match the versions.** The service and the project's `@playwright/test` must
be the same version: set `PLAYWRIGHT_VERSION` to the one in the project's
`package.json`, with `roke settings edit`, and start the project again (the
service's image is built the first time).

**Reach your app by the box's name.** The browsers run in the service, so
`localhost` is the service itself: they reach a dev server in the box at
`http://box:PORT`, and it must listen on `0.0.0.0`. In `playwright.config.ts`:

```ts
use: {
  baseURL: process.env.PW_TEST_CONNECT_WS_ENDPOINT
    ? "http://box:3000"
    : "http://localhost:3000",
},
```

Dev servers that check the host name need to accept `box`, such as Vite's
`server.allowedHosts` or Next.js's `allowedDevOrigins`.

**Data**: none.

**Settings**

| Variable | Default |
|---|---|
| `PLAYWRIGHT_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project. Make it the project's `@playwright/test` version |
