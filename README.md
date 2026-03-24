# img2

Image converter with drag & drop support.

## Installation

### Homebrew (recommended)

```bash
brew tap chaitat/homebrew-img2
brew install img2
```

This will automatically install ImageMagick if not already installed.

### Manual

1. Install [ImageMagick](https://imagemagick.org/):
   ```bash
   brew install imagemagick
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python img2.py
   ```

## Usage

1. Select output format (jpg, png, gif, webp, avif, ico)
2. Set quality (1-100)
3. Optionally resize:
   - No resize
   - Fix width (enter pixel value)
   - Fix height (enter pixel value)
4. Drag and drop images or folders onto the app
5. Converted images are saved in `img2<format>` folder next to original

## License

MIT
