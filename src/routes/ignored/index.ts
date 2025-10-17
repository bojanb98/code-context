import { Elysia, t } from "elysia";
import { IgnoredFilesService } from "../../services/ignored-files.service";
import { logger } from "../../logger";

export const ignoredRoutes = new Elysia({ prefix: "/api/ignored" })
  .post(
    "/",
    async ({ body }: { body: { path: string; pattern: string } }) => {
      return await IgnoredFilesService.addPattern(body.path, body.pattern);
    },
    {
      body: t.Object({
        path: t.String({
          description: "Project path to add ignored pattern to",
        }),
        pattern: t.String({
          description: "Git-style ignore pattern to add",
        }),
      }),
      response: t.Object({
        path: t.String(),
        pattern: t.String(),
        totalPatterns: t.Numeric(),
        added: t.Boolean(),
      }),
    },
  )
  .get(
    "/",
    async ({ query }) => {
      const result = await IgnoredFilesService.listPatterns(query.path);

      if (query.path) {
        return {
          patterns: result.patterns || [],
          projectPath: result.projectPath || "",
          totalPatterns: result.totalPatterns || 0,
        };
      } else {
        return {
          currentProject: result.currentProject || {
            path: "",
            patterns: [],
            totalPatterns: 0,
          },
          allProjects: result.allProjects || [],
        };
      }
    },
    {
      query: t.Object({
        path: t.Optional(
          t.String({
            description: "Optional project path to list patterns for",
          }),
        ),
      }),
      response: t.Union([
        t.Object({
          patterns: t.Array(t.String()),
          projectPath: t.String(),
          totalPatterns: t.Numeric(),
        }),
        t.Object({
          currentProject: t.Object({
            path: t.String(),
            patterns: t.Array(t.String()),
            totalPatterns: t.Numeric(),
          }),
          allProjects: t.Array(
            t.Object({
              path: t.String(),
              count: t.Numeric(),
            }),
          ),
        }),
      ]),
    },
  )
  .delete(
    "/",
    async ({ body }: { body: { path: string; pattern: string } }) => {
      return await IgnoredFilesService.removePattern(body.path, body.pattern);
    },
    {
      body: t.Object({
        path: t.String({
          description: "Project path to remove ignored pattern from",
        }),
        pattern: t.String({
          description: "Git-style ignore pattern to remove",
        }),
      }),
      response: t.Object({
        path: t.String(),
        pattern: t.String(),
        totalPatterns: t.Numeric(),
        removed: t.Boolean(),
      }),
    },
  )
  .onError(({ error, code }) => {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    logger.error(`Ignored routes error: ${errorMessage}`);

    if (code === "VALIDATION") {
      return {
        error: "Invalid request parameters",
        details: errorMessage,
      };
    }

    return {
      error: errorMessage,
    };
  });