cask "img2" do
  # sha256 must be updated after each release
  # run: shasum -a 256 img2.dmg
  version "1.0.0"
  sha256 "UPDATE_WITH_ACTUAL_SHA256"

  url "https://github.com/chaitat/img2/releases/download/v#{version}/img2.dmg"
  name "img2"
  desc "Image converter with drag & drop support"
  homepage "https://github.com/chaitat/img2"

  depends_on formula: "imagemagick"

  app "img2.app"
end
