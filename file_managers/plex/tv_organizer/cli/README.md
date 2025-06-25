# TV Organizer CLI

## Quick Start

From project root (`/home/noufal/personal_package`):

```bash
# Check status
python3 tv_organizer.py status

# Scan for duplicates
python3 tv_organizer.py duplicates --scan --report

# Get help
python3 tv_organizer.py --help
```

## Available Commands

### Phase 0: Duplicate Detection ✅
- `duplicates --scan` - Scan directories for duplicate episodes
- `duplicates --report` - Generate detailed duplicate report
- `duplicates --stats` - Show duplicate statistics
- `duplicates --show "ShowName"` - Show duplicates for specific show

### Utility Commands
- `config --show` - Display configuration
- `status` - Show phase status and available commands

### Future Commands 🚧
- `loose --scan` - Phase 1: Find loose episodes (planned)
- `resolve --analyze` - Phase 2: Path resolution (planned)
- `organize --execute` - Phase 3: File organization (planned)

## Output Formats

- **Text** (default): Human-readable reports
- **JSON**: Machine-readable data (`--format json`)

## Documentation

See `../INSTRUCTIONS.md` for comprehensive usage instructions.

## Module Structure

```
tv_organizer/
├── INSTRUCTIONS.md          # Detailed instructions
├── cli/
│   ├── README.md           # This file
│   └── tv_organizer_cli.py # Main CLI interface
├── core/                   # Core logic
├── models/                 # Data models
└── utils/                  # Utilities
```