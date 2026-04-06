import { getCollection, type CollectionEntry } from 'astro:content';

export type Post = CollectionEntry<'posts'>;

export async function getAllPosts(): Promise<Post[]> {
  const posts = await getCollection('posts', ({ data }) => !data.draft);
  return posts.sort(
    (a, b) => b.data.date_saved.valueOf() - a.data.date_saved.valueOf()
  );
}

export async function getFeaturedPosts(): Promise<Post[]> {
  const posts = await getAllPosts();
  return posts.filter((p) => p.data.featured);
}

export async function getPostsByTag(tag: string): Promise<Post[]> {
  const posts = await getAllPosts();
  return posts.filter((p) =>
    p.data.tags.map((t) => t.toLowerCase()).includes(tag.toLowerCase())
  );
}

export async function getPostsBySource(source: string): Promise<Post[]> {
  const posts = await getAllPosts();
  return posts.filter((p) => p.data.source_site === source);
}

export function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}
