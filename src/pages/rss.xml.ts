import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const posts = await getCollection('posts', ({ data }) => !data.draft);
  const sorted = posts.sort((a, b) => b.data.date_saved.valueOf() - a.data.date_saved.valueOf());

  return rss({
    title: 'Gloam — Personal Reading Archive',
    description: 'The best writing from across the web, curated in one place.',
    site: context.site!,
    items: sorted.map((post) => ({
      title: post.data.title,
      pubDate: post.data.date_saved,
      description: post.data.description ?? `Saved from ${post.data.source_site} by ${post.data.original_author}`,
      link: `/posts/${post.id}/`,
      customData: `<author>${post.data.original_author}</author>`,
    })),
  });
}
