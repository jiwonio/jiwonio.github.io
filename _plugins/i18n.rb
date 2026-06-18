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
    LANG_PATH = %r{\A_posts/(#{LANG_DIRS.join('|')})/}i

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
  end

  class Site
    attr_accessor :posts_by_lang, :translations
  end

  Jekyll::Hooks.register :posts, :post_init do |post|
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
    translations = Hash.new { |hash, key| hash[key] = {} }

    site.posts.docs.each do |post|
      lang = post.data["lang"] || default
      by_lang[lang] << post

      key = post.data["translation_key"]
      translations[key][lang] = post if key
    end

    by_lang.each_value { |posts| posts.sort_by! { |doc| -doc.date.to_i } }

    site.posts_by_lang = by_lang
    site.translations = translations
  end

  Jekyll::Hooks.register :site, :pre_render do |site, payload|
    payload["site"]["default_lang"] = I18n.default_lang(site)
    payload["site"]["lang_codes"] = I18n.lang_codes(site)
    payload["site"]["posts_by_lang"] = site.posts_by_lang || {}
    payload["site"]["translations"] = site.translations || {}
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