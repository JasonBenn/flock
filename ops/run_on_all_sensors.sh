#!/usr/bin/env bash

# Requires `brew install parallel`
# Output preserves the ordering below

echo "Working..."
{
    echo common_room_external
    echo study_external
    echo middle_kingdom_kitchen_external
    # echo jasons_room_external
    # echo workshop_arrams_room
    # echo backyard
    # echo roof
} | parallel -k bash $1