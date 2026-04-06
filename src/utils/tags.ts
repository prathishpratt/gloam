import { getAllPosts, type Post } from './posts';

export interface TagCount {
  tag: string;
  count: number;
}

export async function getAllTags(): Promise<TagCount[]> {
  const posts = await getAllPosts();
  const counts: Record<string, number> = {};

  for (const post of posts) {
    for (const tag of post.data.tags) {
      counts[tag] = (counts[tag] ?? 0) + 1;
    }
  }

  return Object.entries(counts)
    .map(([tag, count]) => ({ tag, count }))
    .sort((a, b) => b.count - a.count);
}

export function slugifyTag(tag: string): string {
  return tag.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
}
