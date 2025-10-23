def human_readable_size(size_in_bytes: int) -> str:
    """Convert a file size in bytes to a human-readable format using binary units (KiB, MiB, etc.)."""
    size = size_in_bytes

    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{size:.2f} EiB"
