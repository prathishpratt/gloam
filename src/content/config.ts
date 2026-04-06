import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    source_url: z.string().url(),
    source_site: z.enum([
      'Substack',
      'Medium',
      'Personal Blog',
      'WordPress',
      'Course Page',
      'Other',
    ]),
    original_author: z.string(),
    date_saved: z.coerce.date(),
    date_published: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    cover_image: z.string().optional(),
    featured: z.boolean().default(false),
    draft: z.boolean().default(false),
  }),
});

export const collections = { posts };
