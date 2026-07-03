# I built a spell-checker for the statistics in research papers

*Suggested tags for Dev.to / Medium: qwen, alibabacloud, ai, python, hackathon*

I kept running into the same uncomfortable fact. Somewhere around half of published
psychology papers have at least one number that doesn't add up. It's usually not
fraud. It's tired people making small mistakes. A p-value typed wrong. An average
that can't exist for the sample size. A result called "significant" that, when you
actually check it, isn't.

The strange thing is that these slip through. Reviewers read for the ideas and the
argument, not the arithmetic. Almost nobody sits down and recomputes a p-value by
hand. And the tools that can do it are expensive, closed, and sold to journals, so
they only run after you've already submitted. The one person who'd benefit the most,
the author about to hit submit, gets nothing.

So I built Rigor. You paste your paper, or drop in a PDF, and it checks the numbers
for you in a few seconds.

## What it checks

Four things, and they each catch a different kind of slip.

It recomputes every p-value from the test statistic. If you wrote p < .001 but the
math says p = .06, it tells you.

It runs the GRIM test on averages. The mean of ten whole-number answers can't be
3.45. Small checks like that catch typos, and sometimes worse.

It compares the degrees of freedom to the sample size. If a test needs more people
than the study actually collected, something is mislabeled.

And it reads the claims. This is the part I'm proudest of. It looks at whether the
words match the numbers, like calling a result significant when the recomputed value
says it isn't.

Every finding comes with a plain explanation and a suggestion for what to do next,
not just a red mark.

## The question I was afraid of

Early on I kept asking myself whether this was just ChatGPT with a nice screen on
top. That question kills a lot of AI projects, and it deserved a real answer.

Here's how I made sure it wasn't. Qwen, the model, only reads. Its one job is to pull
the numbers and claims out of messy writing. It never decides if something is right
or wrong. Every verdict comes from plain math, exact statistics that can't be made
up. If the model misreads something, the worst case is a flag you can dismiss. It can
never invent a wrong answer, because it never gives an answer at all. The math does.

That split, where the model reads and the math judges, is the whole idea.

## Where Qwen came in

I used Qwen through Alibaba Cloud's Model Studio. The part only a good model can do
is read real, free-form scientific writing and pull the statistics out as clean data.
I used Qwen's function calling for this, so instead of hoping it hands back tidy text
I can parse, it fills in a proper structured form. It's more reliable, and honestly
it just feels more deliberate.

I used Qwen again for the claim checking, and I tied it back to the results the math
had already confirmed, so the strong flags are provable, not opinions.

## Turning it into a real agent

For a while Rigor was a straight line. Extract, check, report. Useful, but that's a
pipeline, not an agent. So I gave Qwen the checks as tools and let it run its own
loop. Now it reads the paper, decides what to check, calls the tools itself, thinks
about the results, and then tells you whether the problems look like one-off typos or
something more systematic.

My favorite part is that you can watch it happen. There's a live log in the app that
streams each step as it goes: reading, calling grim_test, calling recompute_pvalue,
reasoning, then the verdict. Seeing it work is what made the whole thing click for
me. It's clearly doing something, not pretending to.

## The mistake that taught me the most

I ran an early version on some real papers, feeling pretty smart, and it flagged a
measurement of 6.07 micrometres as an impossible average. That's nonsense. GRIM only
applies to whole-number ratings, not physical measurements. My extraction was too
eager.

That was a good wake-up. I tightened it so it only checks what it should, added a few
guards, and now it stays quiet when a paper is out of its depth. Being careful turned
out to matter as much as being clever.

## Does it work on real papers?

Yes, and I have a favorite example. I ran it on a published geology paper about rock
erosion. It flagged a correlation the authors reported "across the four rock types"
as significant. With only four data points, that's a shaky claim. I went and read the
paper's own methods to be sure, and yes, four rock types, four points. Rigor caught
it on its own, and it was right to.

On a small test set it catches every planted error and never flags a clean one. That
set isn't huge yet, and I say so in the app. On long, messy real papers it can be
noisier, which is exactly why there's a human review step. It flags, you decide, and
you dismiss anything it got wrong before you export the report.

## Running it on Alibaba Cloud

The whole thing runs on Alibaba Cloud, in a container on a small server in Singapore,
with Qwen doing the reading. It's open source, and I also wrapped the checks in an MCP
server, so other AI agents can call them too. Rigor ended up being a small building
block, not just a website.

## What I'd pass on

If you build with a model, use it for the one thing only it can do, which is making
sense of human writing, and let ordinary code own anything that has to be correct.
That line is what turns a demo into something people can actually trust.

Rigor is free and open source. The code is at
https://github.com/usv240/rigor, and you can try the live version, paste a paper, and
watch it work.
