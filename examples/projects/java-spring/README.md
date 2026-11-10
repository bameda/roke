# Example: Java / Spring Boot

For a Spring Boot service with PostgreSQL and Kafka.

## What it sets up

- **`project.env`**: `postgres` and `kafka`, port 8080, and Serena.
- **`compose.yaml`**: the Spring properties for the database and Kafka, as
  environment variables, and Spring Boot's Docker Compose support turned
  off (see below).
- **`AGENTS.md`**: building and testing, and which tests cannot run here.

## In the project

Add a `mise.toml`:

```toml
[tools]
java = "temurin-21"
```

Build with the project's wrapper (`./mvnw` or `./gradlew`).

Spring Boot reads `SPRING_DATASOURCE_URL`, `SPRING_KAFKA_BOOTSTRAP_SERVERS`
and the rest from the environment, so `compose.yaml` connects the app to
the box's services without changing `application.yml`.

**What cannot run in the box: anything that starts containers.** There is
no Docker inside, on purpose, so:

- Tests using [Testcontainers](https://testcontainers.com/) fail with
  *Could not find a valid Docker environment*. Run them on your host, and
  let the agent run the rest. Tagging them (for example with JUnit's
  `@Tag("containers")`) makes it easy to exclude them in the box.
- Spring Boot's Docker Compose support (`spring-boot-docker-compose`)
  would try to start the project's `compose.yaml` on boot. It is turned off
  through `SPRING_DOCKER_COMPOSE_ENABLED=false`; the box's services replace
  it.

## Check it

From `roke shell`:

```bash
./mvnw test             # or ./gradlew test
./mvnw spring-boot:run  # then http://127.0.0.1:8080
```
