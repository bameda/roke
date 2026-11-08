# Playwright's browsers as a server the box connects to. The official image
# has the browsers and every system library they need; the Playwright
# package is installed here, at build time, since the service has no route
# out. Its version must be the one the image's browsers are for.
ARG PLAYWRIGHT_VERSION
FROM mcr.microsoft.com/playwright:v${PLAYWRIGHT_VERSION}-noble

ARG PLAYWRIGHT_VERSION
WORKDIR /opt/playwright-server
RUN set -eux; \
    test -n "${PLAYWRIGHT_VERSION}"; \
    npm init -y >/dev/null; \
    npm install --no-audit --no-fund "playwright@${PLAYWRIGHT_VERSION}"; \
    chown -R pwuser:pwuser /opt/playwright-server

USER pwuser
EXPOSE 3000
CMD ["./node_modules/.bin/playwright", "run-server", "--port", "3000", "--host", "0.0.0.0"]
