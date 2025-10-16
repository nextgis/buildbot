variable "REGISTRY" { default = "harbor.nextgis.net/ngqgis/ngqgis" }

group "base" {
  targets = [
    "ubuntu-worker-focal",
    "ubuntu-worker-jammy",
    "ubuntu-worker-noble",
    "astra-worker-17",
    "flatpak-worker-kde-515-2408",
    # "crosscompile-worker-r25c",
  ]
}

target "common" {
  pull = true
  platforms = ["linux/amd64"]
}

# Ubuntu Focal
target "ubuntu-worker-focal" {
  inherits   = ["common"]
  context    = "."
  dockerfile = "ubuntu-worker-focal/Dockerfile"
  tags       = ["${REGISTRY}/ubuntu-worker:focal"]
}

# Ubuntu Jammy
target "ubuntu-worker-jammy" {
  inherits   = ["common"]
  context    = "."
  dockerfile = "ubuntu-worker-jammy/Dockerfile"
  tags       = ["${REGISTRY}/ubuntu-worker:jammy"]
}

# Ubuntu Noble
target "ubuntu-worker-noble" {
  inherits   = ["common"]
  context    = "."
  dockerfile = "ubuntu-worker-noble/Dockerfile"
  tags       = ["${REGISTRY}/ubuntu-worker:noble"]
}

# Astra Linux 1.7
target "astra-worker-17" {
  inherits   = ["common"]
  context    = "."
  dockerfile = "astra-worker-1.7/Dockerfile"
  tags       = ["${REGISTRY}/astra-worker:1.7"]
}

# Flatpak KDE 5.15
target "flatpak-worker-kde-515-2408" {
  inherits   = ["common"]
  context    = "."
  dockerfile = "flatpak-worker-kde-5.15-24.08/Dockerfile"
  tags       = ["${REGISTRY}/flatpak-worker:kde-5.15-24.08"]
}

target "crosscompile-worker-r25c" {
  inherits   = ["common"]
  context    = "."
  dockerfile = "crosscompile-worker/Dockerfile"
  tags       = ["${REGISTRY}/crosscompile-worker:r25c"]
  depends_on = ["ubuntu-worker-jammy"]
}
