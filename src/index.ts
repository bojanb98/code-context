import { Elysia, t } from "elysia";
import { logger } from "./logger";
import { indexRoutes } from "./routes/index";
import { searchRoutes } from "./routes/search";
import { configRoutes } from "./routes/config";
import { ignoredRoutes } from "./routes/ignored";
import openapi from "@elysiajs/openapi";

const statusRoutes = new Elysia({ prefix: "/api/status" }).get(
  "/",
  () => ({
    message: "Claude Context API is running",
    timestamp: new Date().toISOString(),
  }),
  {
    response: t.Object({
      message: t.String(),
      timestamp: t.String(),
    }),
  },
);

const app = new Elysia({
  name: "Claude Context API",
})
  .use(openapi())
  .use(statusRoutes)
  .use(indexRoutes)
  .use(searchRoutes)
  .use(configRoutes)
  .use(ignoredRoutes)
  .onError(({ error, code }) => {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    logger.error(`Request error: ${errorMessage}`);
    if (code === "VALIDATION") {
      return {
        error: "Invalid request parameters",
        details: errorMessage,
      };
    }
    return {
      error: errorMessage,
    };
  })
  .listen({
    port: process.env.PORT || 3000,
    hostname: process.env.HOST || "localhost",
  });

logger.info(
  `Claude Context API server started on http://${app.server?.hostname}:${app.server?.port}`,
);

export default app;
