# ADR 0005: Deploy on Alibaba Cloud ECS with Docker

Status: Accepted

## The problem

The project has to run on Alibaba Cloud, and we need a deploy that is reliable, easy
to reproduce, and simple to show on camera for the demo. We also cannot afford to
let a running server quietly run up cost.

## The decision

Package the app with Docker and run it on a small Alibaba Cloud ECS instance in
Singapore, close to the Qwen endpoint for low latency. Set an automatic release date
on the instance so it shuts itself down and cannot keep billing after the hackathon.

## Why it is good, and the trade-off

The same Docker image runs locally and in the cloud, so there are no surprises. A
plain VM is easy to understand, easy to redeploy, and gives us a real public URL to
demo. The auto-release date caps the cost without us having to remember anything.

Trade-off: a VM costs a little each day, unlike pay-per-request serverless. For a
short-lived hackathon project with a hard end date, that is the simpler, safer
choice.
