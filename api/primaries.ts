/**
 * /api/primaries — Unified primaries search endpoint
 * 
 * Searches TRUTH channel data: SEC filings, Temple posts, arXiv papers.
 * No LLM transformation. Raw token extraction only.
 * 
 * Query params:
 *   q - search query
 *   source_type - sec | temple | arxiv
 *   company - SEC company filter
 *   form - SEC form type (10-K, 10-Q, etc.)
 *   min_ai_score - minimum AI keyword score
 *   min_compute_score - minimum compute signal score
 *   sort - date | ai_score | compute_score
 *   limit - max results (default 30)
 */

import type { Context } from "hono";
import { readFileSync, existsSync, readdirSync } from "fs";
import { join } from "path";

interface SEC filing {
  company: string;
  cik: string;
  form: string;
  date: string;
  url: string;
  ai_score: number;
  compute_score: number;
  content: string;
}

interface TemplePost {
  id: string;
  title: string;
  content: string;
  published: string;
  link: string;
  source_type: string;
}

interface ArxivPaper {
  id: string;
  title: string;
  summary: string;
  authors: string[];
  published: string;
  link: string;
  categories: string[];
}

const PRIMARIES_DIR = "/home/workspace/primaries";

export default async (c: Context) => {
  const query = c.req.query("q") || "";
  const sourceType = c.req.query("source_type") || "";
  const company = c.req.query("company") || "";
  const form = c.req.query("form") || "";
  const minAiScore = parseInt(c.req.query("min_ai_score") || "0");
  const minComputeScore = parseInt(c.req.query("min_compute_score") || "0");
  const sort = c.req.query("sort") || "date";
  const limit = parseInt(c.req.query("limit") || "30");

  const results: any[] = [];
  let stats = {
    sec_filings: 0,
    temple_posts: 0,
    arxiv_papers: 0,
    total_cached: 0,
  };

  try {
    // Load SEC filings
    if (!sourceType || sourceType === "sec") {
      const secDir = join(PRIMARIES_DIR, "sec");
      if (existsSync(secDir)) {
        const ciks = readdirSync(secDir).filter(d => d.startsWith("000"));
        for (const cik of ciks.slice(0, 50)) {
          const cikDir = join(secDir, cik);
          const files = readdirSync(cikDir).filter(f => f.endsWith(".json"));
          for (const file of files.slice(0, 10)) {
            try {
              const data = JSON.parse(readFileSync(join(cikDir, file), "utf-8"));
              if (Array.isArray(data)) {
                for (const item of data) {
                  stats.sec_filings++;
                  if (company && !item.company?.toLowerCase().includes(company.toLowerCase())) continue;
                  if (form && item.form !== form) continue;
                  if (item.ai_score < minAiScore) continue;
                  if (item.compute_score < minComputeScore) continue;
                  if (query) {
                    const text = JSON.stringify(item).toLowerCase();
                    if (!text.includes(query.toLowerCase())) continue;
                  }
                  results.push({
                    source_type: "sec",
                    title: `${item.company} - ${item.form}`,
                    snippet: item.content?.slice(0, 200) || "",
                    date: item.date,
                    source_url: item.url,
                    company: item.company,
                    form: item.form,
                    ai_score: item.ai_score,
                    compute_score: item.compute_score,
                  });
                }
              }
            } catch {}
          }
        }
      }
    }

    // Load Temple posts
    if (!sourceType || sourceType === "temple") {
      const templeFile = join(PRIMARIES_DIR, "temple/temple_posts.json");
      if (existsSync(templeFile)) {
        const posts = JSON.parse(readFileSync(templeFile, "utf-8"));
        if (Array.isArray(posts)) {
          for (const post of posts) {
            stats.temple_posts++;
            if (query) {
              const text = (post.title + " " + post.content).toLowerCase();
              if (!text.includes(query.toLowerCase())) continue;
            }
            results.push({
              source_type: "temple",
              title: post.title,
              snippet: post.content?.slice(0, 200) || "",
              date: post.published || "",
              source_url: post.link,
            });
          }
        }
      }
    }

    // Load arXiv papers
    if (!sourceType || sourceType === "arxiv") {
      const arxivDir = join(PRIMARIES_DIR, "arxiv");
      if (existsSync(arxivDir)) {
        const categories = readdirSync(arxivDir).filter(d => d.startsWith("cs"));
        for (const cat of categories) {
          const catDir = join(arxivDir, cat);
          if (!existsSync(catDir)) continue;
          const files = readdirSync(catDir).filter(f => f.endsWith(".json"));
          for (const file of files.slice(0, 200)) {
            try {
              const paper = JSON.parse(readFileSync(join(catDir, file), "utf-8"));
              stats.arxiv_papers++;
              if (query) {
                const text = (paper.title + " " + paper.summary).toLowerCase();
                if (!text.includes(query.toLowerCase())) continue;
              }
              results.push({
                source_type: "arxiv",
                title: paper.title,
                snippet: paper.summary?.slice(0, 200) || "",
                date: paper.published,
                source_url: paper.link,
                authors: paper.authors,
              });
            } catch {}
          }
        }
      }
    }

    stats.total_cached = stats.sec_filings + stats.temple_posts + stats.arxiv_papers;

    // Sort results
    if (sort === "date") {
      results.sort((a, b) => (b.date > a.date ? 1 : -1));
    } else if (sort === "ai_score") {
      results.sort((a, b) => (b.ai_score || 0) - (a.ai_score || 0));
    } else if (sort === "compute_score") {
      results.sort((a, b) => (b.compute_score || 0) - (a.compute_score || 0));
    }

    return c.json({
      query: { q: query, source_type: sourceType, company, form },
      total: results.length,
      results: results.slice(0, limit),
      stats,
    });
  } catch (error: any) {
    return c.json({ error: error.message }, 500);
  }
};
