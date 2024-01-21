# Prompts

Main folder where we store the prompts.

## Assistant

Assistant has custom logic as it needs to maintain an user profile and hold real-time status of requests.
The main reason to divide the logic is that we want assistant to be the interface with the users, so it can't be general, we want to manage a user-profile autonomously as this will give us a lot of information from the user.

## System

System has a general logic that all the agents need to follow, the idea behind that is to be able to have the same processes running than on our assistant for any new Agent.

## Thought

To retrieve the relevant information from memory, perform intermediate thought steps and finally provide a good thought.

## Context

To maintain the relevant context without forgetting the on-going task.

## Data storage

To save relevant information on the long term memory, this info will be used later to construct the thoughts.