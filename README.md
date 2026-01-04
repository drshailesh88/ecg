# ECG Guru

> An electrophysiologist in every practitioner's pocket

**ECG Guru** is an AI-powered ECG analysis and teaching platform that serves everyone from village RMPs to practicing electrophysiologists. It's part of the DocAssist ecosystem of tools for Indian healthcare practitioners.

## The Problem

- ECG interpretation is difficult and takes years to master
- Existing apps like PM Cardio cater mainly to beginners
- Advanced features (VT vs SVT, pathway localization) are not available
- No tool lets you "chat with your ECG"
- Most solutions require internet connectivity
- Nothing integrates with clinical workflows

## The Solution

ECG Guru provides:

- **Multi-level Analysis**: From "is this normal?" to "where is this accessory pathway?"
- **Chat Interface**: Talk to your ECG in natural language
- **Offline-First**: Works in villages with no internet
- **Educational Mode**: Learn as you analyze
- **Integration**: Works with EMR, Dora (medical RAG), and Appointments

## Target Users

| Level | User | Primary Need |
|-------|------|--------------|
| 1 | RMPs, Village Practitioners | Is this dangerous? Need referral? |
| 2 | MBBS Students, Residents | Learn ECG interpretation |
| 3 | MD/DM Cardiology | Differential diagnosis |
| 4 | Cardiologists, EPs | Pathway localization, VT vs SVT |

## Features

### MVP (Phase 1)
- [x] ECG image upload (file, camera, clipboard)
- [x] Basic analysis (rate, rhythm, intervals)
- [x] Chat interface for Q&A
- [x] Structured analysis report
- [x] Offline operation

### Core Intelligence (Phase 2)
- [ ] Lead extraction and digitization
- [ ] Precise interval measurements
- [ ] Chamber enlargement detection
- [ ] Ischemia localization
- [ ] Conduction abnormality classification

### Advanced Analysis (Phase 3) - *The Differentiator*
- [ ] VT vs SVT with aberrancy differentiation
- [ ] SVT mechanism classification
- [ ] Accessory pathway localization
- [ ] VT origin localization
- [ ] Channelopathy detection

### Integration & Scale (Phase 4)
- [ ] EMR integration
- [ ] Dora knowledge base connection
- [ ] Educational modules
- [ ] Hindi localization

## Technology Stack

- **UI**: Flet (cross-platform Python)
- **AI**: Ollama + Qwen models (local inference)
- **Vision**: LLaVA or similar for ECG image analysis
- **Database**: SQLite + ChromaDB
- **Language**: Python 3.11+

## Quick Start

```bash
# Clone the repository
git clone https://github.com/drshailesh88/ecg.git
cd ecg

# Install dependencies
pip install -e .

# Install Ollama and models
ollama pull qwen2.5:7b
ollama pull llava:7b

# Run the app
python -m ecg_guru
```

## Development

This project uses **spec-kit** for specification-driven development and **ralph-wiggum** for iterative AI-assisted implementation.

```bash
# Install spec-kit
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# View specifications
ls .specify/

# Run tests
pytest tests/
```

### Project Structure

```
ecg/
├── .specify/                # Spec-kit specifications
│   ├── constitution.md      # Core principles
│   ├── requirements/        # Feature requirements
│   ├── plans/              # Implementation plans
│   └── tasks/              # Task breakdowns
├── src/
│   ├── ui/                 # Flet UI components
│   ├── core/               # ECG processing engine
│   ├── ai/                 # AI/ML pipelines
│   ├── knowledge/          # Knowledge base
│   └── integrations/       # External connectors
├── tests/
├── docs/
├── CLAUDE.md               # AI development directives
└── README.md
```

## DocAssist Ecosystem

ECG Guru integrates with:

| Product | Repository | Purpose |
|---------|------------|---------|
| **EMR** | [drshailesh88/emr](https://github.com/drshailesh88/emr) | Patient records, clinical context |
| **Appointments** | [drshailesh88/appointment_system](https://github.com/drshailesh88/appointment_system) | Scheduling, urgent referrals |
| **Dora** | [drshailesh88/Dora](https://github.com/drshailesh88/Dora) | Guidelines, treatment protocols |
| **Academic Writing** | [drshailesh88/cursor_for_academic_writing](https://github.com/drshailesh88/cursor_for_academic_writing) | Case study documentation |

## Why Different from PM Cardio?

| Aspect | PM Cardio | ECG Guru |
|--------|-----------|----------|
| Target Users | Beginners | All levels (RMP to EP) |
| Analysis Depth | Basic | Pathway localization |
| Teaching Mode | Limited | Comprehensive |
| Integration | Standalone | Full DocAssist suite |
| Offline | Unknown | Complete offline |
| Localization | Global | India-first |

## Vision

> "I want a cardiologist with years of practice of electrophysiology living inside mobile devices of every practitioner that is seeing patients who are coming with their ECGs."

ECG Guru aims to democratize expert-level ECG interpretation, making it accessible to every healthcare practitioner regardless of location or resources.

## Contributing

This project is under active development. Contributions welcome!

## License

[To be determined]

## Acknowledgments

- Built using the DocAssist ecosystem architecture
- Powered by Ollama and open-source AI models
- Designed for Indian healthcare practitioners

---

*ECG Guru: Because every practitioner deserves an electrophysiologist's expertise.*
