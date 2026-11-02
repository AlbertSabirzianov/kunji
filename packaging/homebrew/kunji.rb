# Homebrew formula TEMPLATE. Copy into your tap repo (testwithsuraj/homebrew-tap,
# file Formula/kunji.rb), fill in the sha256 from SHA256SUMS.txt, then users run:
#   brew install testwithsuraj/tap/kunji
class Kunji < Formula
  desc "Bring your own key. Every AI model in one clean terminal"
  homepage "https://github.com/testwithsuraj/kunji"
  version "0.1.0"
  license "Apache-2.0"

  on_macos do
    url "https://github.com/testwithsuraj/kunji/releases/download/v0.1.0/kunji-macos-arm64"
    sha256 "REPLACE_WITH_SHA256"
  end

  on_linux do
    url "https://github.com/testwithsuraj/kunji/releases/download/v0.1.0/kunji-linux-x64"
    sha256 "REPLACE_WITH_SHA256"
  end

  def install
    binary = Dir["kunji-*"].first || "kunji"
    bin.install binary => "kunji"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/kunji --version")
  end
end
