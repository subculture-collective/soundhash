# User Onboarding & Interactive Tutorial System

## Overview

SoundHash's comprehensive onboarding system helps new users get started quickly and efficiently. The system includes an interactive wizard, video tutorials, quick-start templates, and contextual help to reduce time-to-value from hours to minutes.

## Features

### 1. Interactive Onboarding Wizard

A 6-step guided wizard that takes users through the essential setup:

1. **Welcome (30 seconds)** - Introduction to SoundHash and key features
2. **Use Case Selection** - Choose between Content Creator, Developer, or Enterprise paths
3. **API Key Generation (2 minutes)** - Create and secure API credentials
4. **First Upload (3 minutes)** - Try audio fingerprinting with a sample file
5. **Dashboard Tour (5 minutes)** - Explore key platform features
6. **Integration (10 minutes, optional)** - Connect SDK or API to your platform

**Location:** `/onboarding`

**Features:**
- Progress tracking with visual indicators
- Milestone completion tracking
- Use case-based personalization
- Skip/resume capability
- Estimated time for each step

### 2. Video Tutorials Library

Comprehensive video tutorials organized by category:

**Categories:**
- Basics
- API
- Features
- SDKs
- Advanced

**Location:** `/tutorials`

**Features:**
- Searchable and filterable content
- Progress tracking per tutorial
- Duration indicators
- Completion badges

### 3. Quick-Start Templates

Pre-built code examples for immediate use:

**Languages Supported:**
- Python (basic upload, batch processing, streaming)
- JavaScript/Node.js
- Go
- cURL/REST API

**Location:** `/tutorials` (Templates tab)

**Features:**
- Copy-to-clipboard functionality
- Syntax highlighting
- Working examples for common use cases
- Integration patterns

### 4. Help Center

Searchable knowledge base with articles organized by category:

**Categories:**
- Basics
- API
- Features
- Support

**Location:** `/tutorials` (Help Center tab)

**Features:**
- Full-text search
- Quick action cards (Documentation, Community, Support)
- Direct links to external resources

### 5. Contextual Help System

In-app tooltips that provide context-sensitive assistance:

**Features:**
- Dismissible tooltips
- Local storage persistence
- Custom positioning
- Programmatic control

**Usage:**
```tsx
// Import from the onboarding components directory
import ContextualTooltip, { useContextualHelp } from '@/components/onboarding/ContextualTooltip'

function MyComponent() {
  const { isTooltipVisible, dismissTooltip } = useContextualHelp()
  
  return (
    <div>
      {isTooltipVisible('my-tooltip') && (
        <ContextualTooltip
          title="Feature Name"
          content="Description of the feature"
          onClose={() => dismissTooltip('my-tooltip')}
        />
      )}
    </div>
  )
}
```

### 6. Product Tour

Interactive spotlight-based tours for feature discovery:

**Features:**
- Element highlighting
- Step-by-step navigation
- Backdrop overlay
- Responsive positioning

**Usage:**
```tsx
import ProductTour from '@/components/onboarding/ProductTour'

const tourSteps = [
  {
    target: '.upload-button',
    title: 'Upload Audio',
    content: 'Click here to upload your first audio file',
    placement: 'bottom',
  },
  // ... more steps
]

<ProductTour
  steps={tourSteps}
  onComplete={() => console.log('Tour completed')}
  onSkip={() => console.log('Tour skipped')}
/>
```

## Backend API

### Endpoints

#### Onboarding Progress

**GET** `/api/v1/onboarding/progress`
- Get user's onboarding progress
- Auto-creates record if doesn't exist

**POST** `/api/v1/onboarding/progress`
- Create or reset onboarding progress

**PATCH** `/api/v1/onboarding/progress`
- Update specific milestones or progress

**Example:**
```json
{
  "current_step": 2,
  "use_case": "developer",
  "api_key_generated": true
}
```

#### Tutorial Progress

**GET** `/api/v1/onboarding/tutorials`
- List all tutorial progress for user

**GET** `/api/v1/onboarding/tutorials/{tutorial_id}`
- Get specific tutorial progress

**POST** `/api/v1/onboarding/tutorials`
- Start tracking a new tutorial

**PATCH** `/api/v1/onboarding/tutorials/{tutorial_id}`
- Update tutorial progress

#### User Preferences

**GET** `/api/v1/onboarding/preferences`
- Get user's UI preferences

**POST** `/api/v1/onboarding/preferences`
- Create preferences

**PATCH** `/api/v1/onboarding/preferences`
- Update preferences

**Example:**
```json
{
  "show_tooltips": true,
  "show_contextual_help": true,
  "auto_start_tours": false,
  "theme": "dark"
}
```

#### Analytics (Admin Only)

**GET** `/api/v1/onboarding/stats`
- Get onboarding completion statistics
- Requires admin privileges

## Database Schema

### Tables

#### `onboarding_progress`
Tracks user's progress through onboarding wizard

**Key Fields:**
- `user_id` - Foreign key to users table
- `current_step` - Current wizard step (0-5)
- `use_case` - Selected use case (content_creator, developer, enterprise)
- `*_completed` - Boolean flags for each milestone
- `custom_data` - JSON field for additional data

#### `tutorial_progress`
Tracks individual tutorial completions

**Key Fields:**
- `user_id` - Foreign key to users table
- `tutorial_id` - Unique tutorial identifier
- `progress_percent` - Completion percentage (0-100)
- `current_step` - Current tutorial step

#### `user_preferences`
Stores UI and onboarding preferences

**Key Fields:**
- `user_id` - Foreign key to users table
- `show_tooltips` - Enable/disable tooltips
- `show_contextual_help` - Enable/disable help system
- `theme` - UI theme preference
- `language` - Localization preference

## Integration Points

### Email Automation

The existing email automation system (`src/email/automation.py`) sends onboarding emails:

- Day 1: Getting started guide
- Day 3: Tips & tricks
- Day 7: Feature highlights

**Coordination with UI Onboarding:**
- Email triggers check `onboarding_progress.is_completed` to avoid sending unnecessary emails
- Emails reference specific onboarding steps that users can complete in the UI
- Email content can be personalized based on `use_case` selection
- Suggested: Add a "Resume Onboarding" button in emails linking to `/onboarding`
- Consider suppressing later emails if user completes onboarding early

### Analytics

Track onboarding metrics:
- Completion rate by use case
- Average time to complete
- Drop-off points
- Most-viewed tutorials

### Personalization

The system personalizes based on:
- Selected use case (content creator, developer, enterprise)
- User preferences
- Completed milestones

## Customization

### Adding New Onboarding Steps

1. Create a new step component in `frontend/components/onboarding/steps/`
2. Add the step to the wizard in `OnboardingWizard.tsx`
3. Add corresponding field to database model
4. Update API models and routes

### Adding New Tutorials

Update the tutorials array in `TutorialsLibrary.tsx`:

```tsx
{
  id: 'new-tutorial',
  title: 'Tutorial Title',
  description: 'Brief description',
  duration: '5:30',
  category: 'Category',
  thumbnail: '/path/to/thumbnail.jpg',
  completed: false,
  tags: ['tag1', 'tag2'],
}
```

### Adding New Templates

Update the templates array in `QuickStartTemplates.tsx`:

```tsx
{
  id: 'template-id',
  name: 'Template Name',
  description: 'Description',
  category: 'Category',
  icon: '🔷',
  language: 'python',
  code: `// Your code here`,
}
```

## Best Practices

### For Users

1. Complete the onboarding wizard to unlock full platform potential
2. Watch relevant video tutorials for your use case
3. Use quick-start templates to accelerate development
4. Enable contextual help for guided feature discovery

### For Developers

1. Track onboarding completion to measure user activation
2. Personalize experience based on use case selection
3. Monitor drop-off points to improve onboarding flow
4. Keep tutorials and templates up-to-date with API changes
5. Use analytics to optimize onboarding sequence

## Migration

To apply the database schema changes:

```bash
# Run the migration
alembic upgrade head

# Or use the specific revision
alembic upgrade d4e8a9b2c1f5
```

**Important Notes:**
- **Downtime:** This migration creates new tables and does not modify existing ones, so it can be run with minimal downtime
- **Prerequisites:** Ensure database backup is taken before running migrations in production
- **Dependencies:** Requires PostgreSQL with JSON support (standard in modern versions)
- **Testing:** Test migration in staging environment first
- **Rollback:** Use `alembic downgrade d4e8a9b2c1f5` if needed to rollback changes

## Future Enhancements

Potential improvements for the onboarding system:

1. **Community Integration**
   - Slack/Discord invitation workflow
   - Community spotlight in help center

2. **Advanced Analytics**
   - A/B testing for onboarding flows
   - Funnel analysis
   - User segmentation

3. **Sample Data**
   - Pre-loaded sample fingerprints
   - Demo matches for exploration

4. **Gamification**
   - Achievement badges
   - Progress leaderboard
   - Milestone rewards

5. **Localization**
   - Multi-language support
   - Region-specific content

6. **AI-Powered Help**
   - Chat-based assistance
   - Contextual suggestions
   - Intelligent search

## Support

For questions or issues with the onboarding system:

- Documentation: https://docs.soundhash.io
- Community: Join our Discord/Slack
- Support: support@soundhash.io

## License

Copyright © 2025 SoundHash. All rights reserved.
