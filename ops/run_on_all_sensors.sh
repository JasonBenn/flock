#!/usr/bin/env bash

# Requires `brew install parallel`
# Output preserves the ordering below

echo "Working..."
{
    echo common_room
    echo study
    echo middle_kitchen
    echo jasons_room
    echo workshop
    echo backyard
    echo roof
} | parallel -k bash $1
