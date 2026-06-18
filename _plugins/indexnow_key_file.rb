# frozen_string_literal: true

# IndexNow API 키 파일을 빌드 결과물 루트에 생성합니다.
#
# _config.yml에 아래 값을 설정하면
#   seo.indexnow_key: "your-key-here"
# 빌드 시 /your-key-here.txt 파일이 생성됩니다.
# (Bing Webmaster Tools → IndexNow에서 키 발급)
#
# 키가 비어 있으면 아무 파일도 만들지 않습니다.

Jekyll::Hooks.register :site, :post_write do |site|
  key = site.config.dig("seo", "indexnow_key")
  next if key.nil? || key.strip.empty?

  output_path = File.join(site.dest, "#{key}.txt")
  File.write(output_path, key)
  Jekyll.logger.info "IndexNow:", "키 파일 생성 → #{key}.txt"
end