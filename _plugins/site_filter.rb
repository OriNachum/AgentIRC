# frozen_string_literal: true

# Site Filter Plugin
#
# Drops pages whose `sites` front matter array does not include
# the current build_site (set in _config.agentirc.yml or _config.culture.yml).
# Pages without a `sites` key are excluded from all builds (fail-safe).

Jekyll::Hooks.register :pages, :post_init do |page|
  site = page.site
  build_site = site.config["build_site"]
  next unless build_site

  page_sites = page.data["sites"]
  unless page_sites.is_a?(Array) && page_sites.include?(build_site)
    page.data["published"] = false
  end
end
