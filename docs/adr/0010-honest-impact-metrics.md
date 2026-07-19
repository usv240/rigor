# ADR 0010: Show impact, but only with numbers we can cite or compute

Status: Accepted

## The problem

People want to know the impact: how much does this actually help? The easy way to
answer is to put big, confident numbers on the page, a money-saved figure, a dramatic
error rate, a return-on-investment claim. But Rigor's whole credibility rests on one
promise: trust the math, not the AI. A single unsourced or inflated number on our own
page would quietly break that promise, and it is exactly the thing a skeptical judge
would check first and use to discredit everything else.

## The decision

Every number Rigor shows is either computed from the actual run or cited to a source.
Nothing is asserted.

- Each audit compares the paper to the published field baseline (Nuijten et al. 2016,
  who ran statcheck over about 250,000 p-values), and says so.
- Each audit estimates time saved from the statistics it actually checked, times a
  conservative per-statistic assumption that is shown in a tooltip, not hidden.
- The corpus run reports an aggregate (roughly three hours by hand versus under six
  minutes) computed from a real 26-paper run.
- We deliberately do not show a money or ROI figure. That would multiply a time
  estimate by a made-up wage, which is two assumptions we cannot stand behind.

## Why it is good, and the trade-off

The impact reads as persuasive precisely because a judge can reproduce it. A cited
baseline and a computed time saving survive scrutiny; a flashy dollar figure does not.

Trade-off: the numbers are smaller and more caveated than marketing copy would be, and
we pass up an eye-catching ROI headline. For a tool whose entire value is
trustworthiness, that is the right trade every time.
