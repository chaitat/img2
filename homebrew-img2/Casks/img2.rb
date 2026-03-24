cask "img2" do
  version "1.0.2"
  sha256 "bac692a0b9f76e28a4c48884942e776125dba11da48040fbbc74977f46453a28"

  url "https://github.com/chaitat/img2/releases/download/v#{version}/img2.dmg"
  name "img2"
  desc "Image converter with drag & drop support"
  homepage "https://github.com/chaitat/img2"

  depends_on formula: "imagemagick"

  app "img2.app"
end
