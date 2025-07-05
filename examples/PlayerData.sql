CREATE TABLE player_data (
    player_handle TEXT NOT NULL PRIMARY KEY,
    display_name TEXT NOT NULL,
    gold INT NOT NULL DEFAULT 0,
    gold_snapshot INT NOT NULL DEFAULT 0,
    total_casts INT NOT NULL DEFAULT 0,
    total_casts_snapshot INT NOT NULL DEFAULT 0,
    last_cast TEXT NOT NULL,
    missing_display_name BOOL NOT NULL DEFAULT false
);
