# Behold-Urwar-Droid-Concepts Architecture

## Application Structure

```mermaid
graph TD
    subgraph Frontend
        UI[Web UI]
    end

    subgraph Routes
        main[main.py<br/>Main Dashboard]
        duck[duck.py<br/>Duck Blueprint]
        routes[routes.py<br/>API Routes]
    end

    subgraph Services
        ref[reference_motion_generation.py<br/>Motion Generation Service]
        playground[open_duck_mini_playground.py<br/>Training Service]
        awd[awd.py<br/>AWD Service]
        deploy[deployment.py<br/>Deployment Service]
    end

    subgraph Submodules
        ref_gen[open_duck_reference_motion_generator]
        duck_playground[open_duck_playground]
        awd_module[awd]
    end

    UI --> main
    UI --> duck
    UI --> routes

    main --> duck
    duck --> ref
    duck --> playground
    duck --> awd
    duck --> deploy

    routes --> ref
    routes --> playground
    routes --> awd
    routes --> deploy

    ref --> ref_gen
    playground --> duck_playground
    awd --> awd_module
end

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant R as Routes
    participant S as Services
    participant SM as Submodules
    participant D as Device

    U->>R: Request Action
    R->>S: Call Service Method
    S->>SM: Execute Submodule Command
    SM-->>S: Return Results
    S-->>R: Process Results
    R-->>U: Return Response

    opt Device Deployment
        R->>S: Deploy Model
        S->>D: Send Model/Commands
        D-->>S: Status/Response
        S-->>R: Deployment Result
        R-->>U: Show Status
    end
```

## Component Responsibilities

### Routes
- **main.py**: Handles main dashboard and learning center views
- **duck.py**: Manages duck-specific pages and actions
- **routes.py**: Provides API endpoints for all duck operations

### Services
- **reference_motion_generation.py**: Generates and manages reference motions
- **open_duck_mini_playground.py**: Handles training and inference in playground
- **awd.py**: Implements AWD functionality and training
- **deployment.py**: Manages device connections and model deployment

### Submodules
- **open_duck_reference_motion_generator**: Generates reference motions
- **open_duck_playground**: Training environment
- **awd**: Advanced walking dynamics implementation

## Duck Types
The application supports two types of ducks:
1. **Open Duck Mini**: Smaller version for testing and development
2. **BDX**: Full-size version for real-world deployment

Each duck type has its own:
- Reference motion generation parameters
- Training configurations
- Deployment settings
- Model storage 