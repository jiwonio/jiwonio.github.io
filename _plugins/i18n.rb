# frozen_string_literal: true

# 다국어 블로그 인프라
#
# - 포스트 URL: ko → /posts/:slug/, 그 외 → /:lang/posts/:slug/
# - translation_key 로 번역본을 묶음
# - 언어별 홈 페이지네이션: /page/2/, /en/page/2/ …
# - Liquid: site.posts_by_lang, site.translations, site.default_lang

module Jekyll
  module I18n
    LANG_DIRS = %w[en ja zh].freeze
    # Jekyll post.path 예: "en/2024/2024-01-01-slug.md" 또는 "_posts/en/..."
    LANG_PATH = %r{(?:\A_posts/|\A)(#{LANG_DIRS.join('|')})/}i

    module_function

    def default_lang(site)
      site.config["default_lang"] || "ko"
    end

    def lang_codes(site)
      codes = site.config["languages"]
      return [default_lang(site)] if codes.nil? || codes.empty?

      codes
    end

    def detect_lang(post, default_lang)
      return post.data["lang"].to_s if post.data["lang"]

      path = post.path.tr("\\", "/")
      match = LANG_PATH.match(path)
      match ? match[1] : default_lang
    end

    def post_slug(post)
      return post.data["slug"].to_s if post.data["slug"]

      basename = File.basename(post.path, ".*")
      basename.sub(/\A\d{4}-\d{2}-\d{2}-/, "")
    end

    def post_permalink(lang, slug, default_lang)
      if lang == default_lang
        "/posts/#{slug}/"
      else
        "/#{lang}/posts/#{slug}/"
      end
    end

    def home_path(lang, page_num, default_lang)
      if lang == default_lang
        page_num == 1 ? "/" : "/page/#{page_num}/"
      else
        page_num == 1 ? "/#{lang}/" : "/#{lang}/page/#{page_num}/"
      end
    end

    def tag_slug(tag_name)
      slug = Jekyll::Utils.slugify(tag_name.to_s.encode("UTF-8"))
      slug unless slug.nil? || slug.empty?
    end

    def description_snippet(lang_meta, site, limit = 120)
      raw = lang_meta["description"] || site.config["description"] || ""
      raw.to_s.gsub(/\s+/, " ").strip[0, limit]
    end

    def build_tag_archives(tags_hash)
      grouped = {}

      tags_hash.each do |tag_name, posts|
        next if posts.nil? || posts.empty?

        slug = tag_slug(tag_name)
        next unless slug

        entry = (grouped[slug] ||= {
          "slug" => slug,
          "title" => tag_name,
          "names" => [],
          "posts" => []
        })

        entry["names"] << tag_name unless entry["names"].include?(tag_name)
        entry["posts"].concat(posts)
      end

      grouped.each_value do |entry|
        entry["posts"].uniq!
        counts = entry["names"].to_h do |name|
          [name, entry["posts"].count { |post| Array(post.data["tags"]).include?(name) }]
        end
        entry["title"] = counts.max_by { |_, count| count }&.first || entry["names"].first
        entry.delete("posts")
      end

      grouped.values.sort_by { |entry| entry["title"].to_s.downcase }
    end

    def build_tag_slug_translations(translations)
      result = {}

      translations.each do |_key, lang_posts|
        next if lang_posts.size < 2

        slugs_by_lang = {}
        lang_posts.each do |lang, post|
          slugs_by_lang[lang] = Array(post.data["tags"]).filter_map do |tag_name|
            slug = tag_slug(tag_name)
            slug ? [tag_name, slug] : nil
          end.uniq(&:last)
        end

        all_langs = slugs_by_lang.keys.sort
        slug_langs = Hash.new { |hash, key| hash[key] = [] }
        slugs_by_lang.each do |lang, pairs|
          pairs.each do |_, slug|
            slug_langs[slug] << lang unless slug_langs[slug].include?(lang)
          end
        end

        all_slugs = slug_langs.keys
        universal_slugs = all_slugs.select { |slug| slug_langs[slug].sort == all_langs }
        non_universal_slugs = all_slugs - universal_slugs
        next if non_universal_slugs.empty?

        lang_sets = non_universal_slugs.to_h { |slug| [slug, slug_langs[slug].sort] }
        disjoint = lang_sets.values.combination(2).all? { |left, right| (left & right).empty? }
        covered_langs = lang_sets.values.flatten.uniq.sort
        next unless disjoint && covered_langs == all_langs

        lang_sets.each do |from_slug, from_langs|
          from_langs.each do |from_lang|
            lang_sets.each do |to_slug, _to_langs|
              next if from_slug == to_slug

              to_slug_langs = slug_langs[to_slug]
              to_slug_langs.each do |to_lang|
                next if from_lang == to_lang

                key = "#{from_lang}|#{from_slug}"
                result[key] ||= {}
                result[key][to_lang] = to_slug
              end
            end
          end
        end
      end

      result
    end
  end

  class Site
    attr_accessor :posts_by_lang, :translations, :tags_by_lang, :tag_archives_by_lang,
                  :tag_slug_translations
  end

  # post_init 이후 Jekyll 기본 permalink가 덮어쓰므로, post_convert에서 최종 URL을 확정합니다.
  Jekyll::Hooks.register :posts, :post_convert do |post|
    site = post.site
    default = I18n.default_lang(site)
    lang = I18n.detect_lang(post, default)
    slug = I18n.post_slug(post)

    post.data["lang"] = lang
    post.data["translation_key"] ||= slug
    post.data["slug"] ||= slug
    post.data["permalink"] = I18n.post_permalink(lang, slug, default)
  end

  Jekyll::Hooks.register :site, :post_read do |site|
    default = I18n.default_lang(site)
    by_lang = Hash.new { |hash, key| hash[key] = [] }
    tags_by_lang = Hash.new { |hash, key| hash[key] = Hash.new { |inner, tag| inner[tag] = [] } }
    translations = Hash.new { |hash, key| hash[key] = {} }

    site.posts.docs.each do |post|
      lang = post.data["lang"] || default
      by_lang[lang] << post

      Array(post.data["tags"]).each do |tag|
        tags_by_lang[lang][tag] << post
      end

      key = post.data["translation_key"]
      translations[key][lang] = post if key
    end

    by_lang.each_value { |posts| posts.sort_by! { |doc| -doc.date.to_i } }
    tags_by_lang.each_value do |tags|
      tags.each_value { |posts| posts.sort_by! { |doc| -doc.date.to_i } }
    end

    tag_archives_by_lang = tags_by_lang.transform_values { |tags| I18n.build_tag_archives(tags) }
    tag_slug_translations = I18n.build_tag_slug_translations(translations)

    site.posts_by_lang = by_lang
    site.tags_by_lang = tags_by_lang
    site.tag_archives_by_lang = tag_archives_by_lang
    site.tag_slug_translations = tag_slug_translations
    site.translations = translations
  end

  Jekyll::Hooks.register :site, :pre_render do |site, payload|
    payload["site"]["default_lang"] = I18n.default_lang(site)
    payload["site"]["lang_codes"] = I18n.lang_codes(site)
    payload["site"]["posts_by_lang"] = site.posts_by_lang || {}
    payload["site"]["tags_by_lang"] = site.tags_by_lang || {}
    payload["site"]["tag_archives_by_lang"] = site.tag_archives_by_lang || {}
    payload["site"]["tag_slug_translations"] = site.tag_slug_translations || {}
    payload["site"]["translations"] = site.translations || {}
  end

  class I18nTagArchiveGenerator < Generator
    safe true
    priority :lowest

    def generate(site)
      default = I18n.default_lang(site)

      I18n.lang_codes(site).each do |lang|
        archives = (site.tag_archives_by_lang || {})[lang] || []
        archives.each do |entry|
          slug = entry["slug"]
          dir = if lang == default
                  File.join("archive", "tag", slug)
                else
                  File.join(lang, "archive", "tag", slug)
                end

          page = PageWithoutAFile.new(site, site.source, dir, "index.html")
          page.data["layout"] = "tag"
          page.data["lang"] = lang
          page.data["archives"] = true
          page.data["title"] = entry["title"]
          page.data["tag_slug"] = slug
          page.data["tag_names"] = entry["names"]
          page.data["image"] = site.config.dig("seo", "default_image")
          lang_meta = site.data.dig("languages", lang) || {}
          tag_heading = lang_meta["tag_heading"] || "Tag"
          snippet = I18n.description_snippet(lang_meta, site)
          page.data["seo_description"] = "#{entry['title']} #{tag_heading} - #{snippet}"
          site.pages << page
        end
      end
    end
  end

  class I18nYearArchiveGenerator < Generator
    safe true
    priority :lowest

    def generate(site)
      default = I18n.default_lang(site)

      I18n.lang_codes(site).each do |lang|
        next if lang == default

        posts = site.posts_by_lang[lang] || []
        posts.map { |post| post.date.year }.uniq.sort.each do |year|
          dir = File.join(lang, "archive", year.to_s)
          page = PageWithoutAFile.new(site, site.source, dir, "index.html")
          page.data["layout"] = "year"
          page.data["lang"] = lang
          page.data["archives"] = true
          page.data["date"] = Date.new(year, 1, 1)
          page.data["image"] = site.config.dig("seo", "default_image")
          lang_meta = site.data.dig("languages", lang) || {}
          year_heading = lang_meta["year_heading"] || "Year"
          snippet = I18n.description_snippet(lang_meta, site)
          page.data["seo_description"] = "#{year} #{year_heading} - #{snippet}"
          site.pages << page
        end
      end
    end
  end

  class I18nPaginationGenerator < Generator
    safe true
    priority :lowest

    def generate(site)
      per_page = (site.config["posts_per_page"] || 5).to_i
      per_page = 5 if per_page < 1
      default = I18n.default_lang(site)

      I18n.lang_codes(site).each do |lang|
        posts = site.posts_by_lang[lang] || []
        total_pages = [(posts.size.to_f / per_page).ceil, 1].max

        (2..total_pages).each do |page_num|
          dir = if lang == default
                  File.join("page", page_num.to_s)
                else
                  File.join(lang, "page", page_num.to_s)
                end

          page = PageWithoutAFile.new(site, site.source, dir, "index.html")
          page.data["layout"] = "home"
          page.data["lang"] = lang
          page.data["page"] = page_num
          page.data["title"] = "Home"
          page.data["image"] = site.config.dig("seo", "default_image")
          page.data["seo_description"] = site.data.dig("languages", lang, "description") || site.config["description"]
          site.pages << page
        end
      end
    end
  end
end