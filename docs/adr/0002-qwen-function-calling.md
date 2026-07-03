# ADR 0002: Use Qwen function calling to extract

Status: Accepted

## The problem

We need clean, structured data out of messy paper text. Asking the model for free
text and then parsing that text with our own code is fragile: small wording changes
break the parser, and we spend our time cleaning up output instead of checking math.

## The decision

Use Qwen's function (tool) calling. We give the model a typed schema for a
`submit_extraction` tool, and it fills in the fields: the statistics, the means, and
the claims. We get structured data back directly, not prose we have to untangle.

## Why it is good, and the trade-off

It is far more reliable than parsing free text, and it uses the Qwen API the way it
is meant to be used. The schema also acts as a contract: the model has to give us
the exact fields our checks need.

Trade-off: it needs a model that supports tool calling. Qwen does, so this costs us
nothing in practice.
