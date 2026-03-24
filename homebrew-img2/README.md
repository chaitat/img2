# homebrew-img2

Homebrew tap for img2 image converter.

## How do I install these formulae?

```bash
brew tap chaitat/img2
brew install img2
```

## Update SHA256

After creating a release, get the SHA256 of the DMG:

```bash
shasum -a 256 img2.dmg
```

Then update `Casks/img2.rb` with the actual SHA256.

## Formulae

- [img2](./Casks/img2.rb) - Image converter with drag & drop support
