# Claude context API 

This is a REST API tool for exposing @zilliz/claude-context-core library as a REST API. It will run in local filesystem.

## Development guidelines

- src folder root
- Use Bun (1.3.0) for running and dependncies
- Use elysia for API
- No auth
- Use winston for logging
- Vertical slice arthicetcure
- Use typescript, avoid any type
- Use elysija built-in validation

## claude-context-core usage example

```js
import { 
  Context, 
  OpenAIEmbedding, 
  MilvusVectorDatabase 
} from '@zilliz/claude-context-core';

// Initialize embedding provider
const embedding = new OpenAIEmbedding({
  apiKey: process.env.OPENAI_API_KEY || 'your-openai-api-key',
  model: 'text-embedding-3-small'
});

// Initialize vector database
const vectorDatabase = new MilvusVectorDatabase({
  address: process.env.MILVUS_ADDRESS || 'localhost:19530',
  token: process.env.MILVUS_TOKEN || ''
});

// Create context instance
const context = new Context({
  embedding,
  vectorDatabase
});

// Index a codebase
const stats = await context.indexCodebase('./my-project', (progress) => {
  console.log(`${progress.phase} - ${progress.percentage}%`);
});

console.log(`Indexed ${stats.indexedFiles} files with ${stats.totalChunks} chunks`);

// Search the codebase
const results = await context.semanticSearch(
  './my-project',
  'function that handles user authentication',
  5
);

results.forEach(result => {
  console.log(`${result.relativePath}:${result.startLine}-${result.endLine}`);
  console.log(`Score: ${result.score}`);
  console.log(result.content);
});
```

## ElysiaJs examples

Rout grouping:
```ts
import { Elysia } from 'elysia'

const users = new Elysia({ prefix: '/user' })
    .post('/sign-in', 'Sign in')
    .post('/sign-up', 'Sign up')
    .post('/profile', 'Profile')

new Elysia()
    .use(users)
    .get('/', 'hello world')
    .listen(3000)
```

Validation:
```ts
import { Elysia } from 'elysia'
import { z } from 'zod'
import * as v from 'valibot'

new Elysia()
	.get('/id/:id', ({ params: { id }, query: { name } }) => id, {
		params: z.object({
			id: z.coerce.number()
		}),
		query: v.object({
			name: v.literal('Lilith')
		})
	})
	.listen(3000)
```
