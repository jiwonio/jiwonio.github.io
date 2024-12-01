### Jekyll localhost [quickstart](https://jekyllrb.com/docs/)

1. Download and install a **Ruby+Devkit** version from [RubyInstaller Downloads](https://rubyinstaller.org/downloads/). Use default options for installation.
2. Run the `ridk install` step on the last stage of the installation wizard. This is needed for installing gems with native extensions. You can find additional information regarding this in the [RubyInstaller Documentation](https://github.com/oneclick/rubyinstaller2#using-the-installer-on-a-target-system). From the options choose `MSYS2 and MINGW development toolchain`.
3. Open a new command prompt window from the start menu, so that changes to the `PATH` environment variable becomes effective. Install Jekyll and Bundler using `gem install jekyll bundler`
4. Check if Jekyll has been installed properly: `jekyll -v`
5. Clone {{ `$ git clone [REPOSITORY]` }}
6. Install {{ `$ bundle install` }}
7. Start {{ `$ bundle exec jekyll serve` }}
- Error {{ `$ bundle add webrick` }}
- Ignore ***baseurl*** {{ `$ bundle exec jekyll serve --baseurl=""` }}
- GitHub Pages gem update {{ `$ bundle update github-pages` }}

### Reference:

- [Jekyll을 사용하여 로컬로 GitHub Pages 사이트 테스트](https://docs.github.com/ko/pages/setting-up-a-github-pages-site-with-jekyll/testing-your-github-pages-site-locally-with-jekyll)
- [Jekyll Installation](https://jekyllrb.com/docs/installation/)
