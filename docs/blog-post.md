# I built a spell-checker for the statistics in research papers

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

Six checks now, and they each catch a different kind of slip.

It recomputes every p-value from the test statistic. If you wrote p < .001 but the
math says p = .06, it tells you, and it flags the ones that flip a result from
significant to not.

It runs the GRIM and GRIMMER tests. GRIM catches an average that can't exist: the mean
of ten whole-number answers can't be 3.45. GRIMMER does the same for the standard
deviation. Small checks like that catch typos, and sometimes worse.

It compares the degrees of freedom to the sample size. If a test needs more people
than the study actually collected, something is mislabeled.

It recomputes a reported effect size (Cohen's d) from the t-statistic, and flags a
mismatch that rounding can't explain.

And it reads the claims, checking whether the words match the numbers, like calling a
result significant when the recomputed value says it isn't.

Every finding comes with a plain explanation and a suggestion for what to do next,
not just a red mark.

## The part I'm proudest of

Most tools stop at "something is wrong." Rigor goes one step further and tells you
which single number is most likely the mistake. A paper's statistics are all linked,
the sample size, the degrees of freedom, the test statistic, the p-value, the mean. So
when several checks fail, Rigor looks for the one correction that would resolve the
most of them, and proves it by re-running the checks with that value substituted. On
the demo paper it says something like "the sample size is the likely typo; fix it and
every flagged test lines up." That is the difference between finding a problem and
knowing how to fix it.

It also puts each paper in context. Every audit compares it to a published baseline
(about one in ten reported p-values is inconsistent, from a study of roughly 250,000 of
them), and estimates the time it just saved you against checking by hand.

## The question I was afraid of

Early on I kept asking myself whether this was just ChatGPT with a nice screen on
top. That question kills a lot of AI projects, and it deserved a real answer.

Here's how I made sure it wasn't. Qwen, the model, only reads. Its one job is to pull
the numbers and claims out of messy writing. It never decides if something is right
or wrong. Every verdict comes from plain math, exact statistics that can't be made up.
You can even prove it: turn the AI off and run the math engine over 530 test cases, and
it still scores 100 percent. If the model misreads something, the worst case is a flag
you can dismiss. It can never invent a wrong answer, because it never gives an answer at
all. The math does.

That split, where the model reads and the math judges, is the whole idea.

## Where Qwen came in

I used Qwen through Alibaba Cloud's Model Studio. The part only a good model can do is
read real, free-form scientific writing and pull the statistics out as clean data. I
used Qwen's function calling for this, so instead of hoping it hands back tidy text I
can parse, it fills in a proper structured form.

Because reading is the only uncertain step, I also let it read a paper a few times and
keep only the numbers the runs agree on, and it shows that agreement as a score. It
turns the one shaky part into a measured number.

## Turning it into a real agent

For a while Rigor was a straight line. Extract, check, report. Useful, but that's a
pipeline, not an agent. So I gave Qwen the checks as tools and let it run its own loop.
Now it reads the paper, decides what to check, calls the tools itself, thinks about the
results, and then tells you whether the problems look like one-off typos or something
more systematic.

My favorite part is that you can watch it happen. There's a live log in the app that
streams each step as it goes: reading, calling grim_test, calling recompute_pvalue,
reasoning, then the verdict.

## The mistake that taught me the most

I ran an early version on some real papers, feeling pretty smart, and it flagged a
measurement of 6.07 micrometres as an impossible average. That's nonsense. GRIM only
applies to whole-number ratings, not physical measurements. My extraction was too
eager. I tightened it so it only checks what it should, and now it stays quiet when a
paper is out of its depth. Being careful turned out to matter as much as being clever.

## Does it work on real papers?

Yes, and I have a favorite example. I ran it on a published geology paper about rock
erosion. It flagged a correlation the authors reported "across the four rock types" as
significant. With only four data points that is a shaky claim, and it recomputes to
about p = 0.08. I read the paper's own methods to be sure, and yes, four rock types,
four points. Rigor caught it on its own.

Then I ran it over 26 real published papers in a single pass, the editorial-review
shape. Recomputing all their reported statistics by hand would take about three hours.
Rigor did it in under six minutes and narrowed the pile to the three papers that needed
a human look, ranking the one I had verified worst of all.

It's honest about its limits, too. On long, messy papers extraction can be noisier,
which is exactly why there's a human review step and the agreement score. It flags, you
decide, and you dismiss anything it got wrong before you export the report.

## Running it on Alibaba Cloud

The whole thing runs on Alibaba Cloud, in a container on a small server in Singapore,
with Qwen doing the reading. It's open source, and it goes where you work: a website, a
command-line tool, a GitHub Action that screens papers on every push, and an MCP server
so other AI agents can call the checks too. Rigor ended up being a small building
block, not just a website.

## What I'd pass on

If you build with a model, use it for the one thing only it can do, which is making
sense of human writing, and let ordinary code own anything that has to be correct. That
line is what turns a demo into something people can actually trust. And for a tool about
integrity, being honest about what it can't do, and only ever showing numbers I can
prove, made it more credible, not less.

Rigor is free and open source. The code is at https://github.com/usv240/rigor, and you
can try the live version, paste a paper, and watch it work.
