# jwjp.github.io

Jekyll 4 based multilingual technical blog archive. Korean (`ko`) posts are the source content, and `en`/`ja`/`zh` translations are grouped by `translation_key`.

- Former custom domain: `blog.jiwon.io` is no longer used.
- Branch: `gh-pages`
- Stack: Ruby 3.3, Jekyll 4, Python 3.11
- Status: low-maintenance archive; GitHub Actions workflows have been removed.

## Structure

```text
_posts/
  ko/{year}/   source posts
  en/{year}/   English translations
  ja/{year}/   Japanese translations
  zh/{year}/   Simplified Chinese translations
```

## Local Checks

```bash
pip install -r scripts/requirements.txt
pip install -e ./scripts
python -m unittest discover -s scripts/tests -v
python scripts/validate_posts.py
```

For a local Jekyll build:

```bash
bundle install
bundle exec jekyll build --baseurl ""
```

## Notes

- `CNAME` was removed with the custom domain shutdown.
- Analytics, AdSense, webmaster verification, and IndexNow settings are disabled in `_config.yml`.
- Automatic GitHub Actions generation, maintenance, deployment, and weekly health jobs were removed.
