## Data Model

### Event
- id (UUID)
- name (string)          # e.g., "Coldplay Concert"
- total_slots (int)      # e.g., 100

### Slot
- id (UUID)
- event_id (FK → Event)
- status (enum: available | locked | booked)

### Booking
- id (UUID)
- slot_id (FK → Slot)
- user_id (string)       # just a fake string for now, no auth
- status (enum: pending | confirmed | failed)
- created_at (timestamp)