cask "img2" do
  version "1.0.0"
  sha256 "513aa559e8316c122593e9d70ddc3102764b5ae83870db9815794b85db75fcd2"

  url "https://github.com/chaitat/img2/releases/download/v#{version}/img2.dmg"
  name "img2"
  desc "Image converter with drag & drop support"
  homepage "https://github.com/chaitat/img2"

  depends_on formula: "imagemagick"

  app "img2.app"
end
