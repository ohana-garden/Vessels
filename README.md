# SHOGHI

Listen: This is a computer program that helps communities build things that last.

Not just get money. Build services that sustain themselves. Services that increase well-being long after the grant money runs out.

Grants are okay. But they're seed money. The real work is growing something that doesn't need grants anymore.

That's what this does.

## What Is This Thing?

Shoghi is named after a guy who coordinated a community once. Now it's a computer program that spawns other computer programs to help your community. These little programs are called agents, which is what we call software that pretends to think.

They don't really think, of course. But they're useful anyway.

So it goes.

## What Does It Do Right This Minute?

It does nine things:

1. **It builds sustainable services**. Community kitchens. Elder care. Childcare. Health clinics. Food systems. Things people need that can eventually pay for themselves through sliding scale fees, memberships, or social enterprise. The computer tracks whether services are becoming self-sufficient or still need help.

2. **It plans transitions from grants to sustainability**. Takes a service that needs $5000 a month to run and figures out how to generate that $5000 through the service itself. Tracks progress. Warns you when things aren't working. This is the main point of the whole thing.

3. **It finds grants**. All of them. Every single boring, bureaucratic, soul-crushing grant opportunity that might give you *seed money* to start a service. Not money to depend on forever. Money to get started.

4. **It writes grant applications**. This is perhaps the most useful thing anyone has ever made a computer do. Grant applications are designed to crush the human spirit. Now a computer can have its spirit crushed instead. And the applications include sustainability plans because that's what funders want anyway.

5. **It makes agents**. You tell it what you need in regular human language. It makes little software robots to do that thing.

6. **It remembers everything**. The agents talk to each other and learn from each other. This is called Community Memory, which is a nice name for a database. They remember what worked, what didn't, and which services became self-sustaining.

7. **It makes new tools when it needs them**. This should probably worry us, but it turns out to be helpful.

8. **It connects to anything**. Government websites, foundation databases, all the places where money hides from communities.

9. **It deploys itself**. You run one command and it sets everything up. This is convenient.

## How To Start It

Here is how you start it:

```bash
./deploy_shoghi.sh --mode production
```

Or this way:

```bash
python3 shoghi.py
```

That's all there is to it.

## How To Talk To It

You talk to it like a person, even though it isn't one:

```
"Shoghi, find grants for elder care in Puna"
"Shoghi, coordinate volunteers for community support"
"Shoghi, what is your status?"
```

It will understand you. Or at least pretend to.

## The Parts

Like everything else, Shoghi is made of smaller things. Here are the smaller things:

### agent_zero_core.py

This is the brain, if it can be called a brain. It reads what you write and spawns agents to do the work. It coordinates all the other agents. It is good at its job.

### dynamic_agent_factory.py

This part makes new agents from scratch. You say "I need help finding grants for elder care in Puna" and it builds you an agent that does exactly that.

It's like a factory. Except the factory builds robots that build other robots.

### community_memory.py

All the agents share their memories here. When one agent learns something, they all learn it. This is more cooperation than most humans ever manage.

The memory uses three technologies at once: vectors, graphs, and event streams. If you don't know what those are, that's fine. They're just fancy databases.

### sustainable_services.py

This is why Shoghi exists.

Most community services start with a grant and die when the grant runs out. This is wasteful and sad.

This part of Shoghi:
- Plans services that can become self-sustaining
- Tracks revenue models: sliding scale fees, memberships, social enterprise, time banking
- Measures financial sustainability: how much of operating costs are covered by earned income
- Measures community well-being: people served, satisfaction scores, actual impact
- Warns you when a service won't become sustainable before grant money runs out
- Identifies successful services that can be replicated elsewhere

It turns grants into seed money for things that last. That's the point.

### grant_coordination_system.py

Grants are how money moves from big organizations to small communities. The process is designed by people who have never needed a grant. It is baroque and cruel and necessary.

But grants should be seed money, not life support.

This part of Shoghi:
- Finds every grant you might qualify for
- Writes complete applications with narratives and budgets (including sustainability plans)
- Fills out all the forms in whatever format they want
- Submits everything
- Tracks it all
- Integrates with sustainable_services.py to ensure grant funds launch services that will survive

It saves communities from drowning in paperwork and from building grant-dependent services. That's worth something.

### adaptive_tools.py

Sometimes an agent needs a tool that doesn't exist yet. This part makes that tool.

The tools make other tools. It's tools all the way down.

### universal_connector.py

This connects to everything:
- Government websites that were designed in 2003
- Foundation databases that require Flash
- PDF forms that hate you
- APIs that were documented once, badly

It just connects. It doesn't complain.

### auto_deploy.py

This deploys itself to wherever it needs to run. Cloud servers, local computers, somewhere in between.

It makes containers. It scales up when it's busy. It scales down when it's not. It monitors itself. It heals itself when it breaks.

Computers taking care of computers. What could go wrong?

### shoghi_interface.py

This is the part you talk to. You use regular human language. It figures out what you mean and builds what you need.

No configuration. No setup. No three-hundred-page manual.

You just describe what you want and it happens.

## Requirements

You need these things:

- Python 3.9 or newer
- Docker if you want containers
- 4 gigabytes of RAM
- An internet connection
- Hope

## An Example

Here is how you would use this:

```python
# Start it
shoghi = ShoghiPlatform()
shoghi.start()

# Find grants
result = shoghi.process_request("find grants for elder care in Puna")

# The grants are found now

# Generate applications
applications = shoghi.grant_system.generate_all_applications()

# Submit them
submissions = shoghi.grant_system.submit_everything()
```

That's all there is to it.

The applications are written now. The forms are filled out. Everything is submitted.

You didn't have to spend three weeks learning to speak bureaucrat.

## Another Example

Say you need to coordinate volunteers:

```python
result = shoghi.process_request("coordinate volunteers for community support")
```

It makes agents that coordinate volunteers. They share information through Community Memory. They get better at it over time.

## Building Something Sustainable

Here is how you would build a service that lasts:

```python
from sustainable_services import SustainableServicesOrchestrator, ServiceType, RevenueModel

# Start the orchestrator
orchestrator = SustainableServicesOrchestrator()

# Create a community kitchen with seed grant funding
kitchen = orchestrator.create_service(
    name="Puna Community Kitchen",
    service_type=ServiceType.FOOD_SYSTEMS,
    description="Pay-what-you-can community meals",
    monthly_operating_cost=5000,  # Rent, supplies, utilities
    seed_grant_amount=60000  # One year runway
)

# Add revenue strategies
orchestrator.add_revenue_strategy(
    service_id=kitchen.id,
    revenue_model=RevenueModel.SLIDING_SCALE_FEES,
    description="Suggested $8/meal, pay what you can",
    target_monthly_revenue=3000,  # 500 meals at avg $6
    timeline_months=6,
    implementation_steps=[
        "Set up payment system",
        "Train volunteers on sliding scale conversations",
        "Market to community"
    ]
)

orchestrator.add_revenue_strategy(
    service_id=kitchen.id,
    revenue_model=RevenueModel.SERVICE_CONTRACTS,
    description="Catering for local events",
    target_monthly_revenue=2000,
    timeline_months=9,
    implementation_steps=[
        "Get health permits",
        "Build catering menu",
        "Network with event organizers"
    ]
)

# Track well-being impact, not just money
orchestrator.add_wellbeing_metric(
    service_id=kitchen.id,
    metric_name="food_security",
    description="Households with reliable meal access",
    target_value=200,
    measurement_method="Monthly survey"
)

# Get sustainability report
report = orchestrator.generate_sustainability_report(kitchen.id)
print(f"Self-sufficiency: {report['financial_health']['self_sufficiency_percentage']}%")
print(f"Months to sustainability: {report['financial_health']['estimated_months_to_sustainability']}")
print(f"Recommendations: {report['recommendations']}")
```

The computer tracks whether you're on track. It warns you if the grant will run out before the service becomes sustainable. It tells you what to adjust.

This is better than just getting a grant and hoping.

## What It's For

Here is what it's for:

- **Communities that want to build things that last**. Not just services that survive on grants year to year. Services that become self-sustaining and serve the community for decades. Community kitchens that generate revenue. Elder care co-ops that members support. Childcare centers that run on sliding scale fees. Things that work.

- **People tired of the grant treadmill**. Chasing grants every year is exhausting. Building a service that pays for itself is better. This helps you do that.

- **Elders who need care**. Puna has a lot of elders. They need support. Support needs funding initially, then it needs a sustainable model. This provides both.

- **Anyone trying to do something good that will still be there in ten years**. Communities are complicated. Coordinating them is hard. Making things sustainable is harder. This makes it less hard.

## Configuration

There is no configuration.

The program configures itself based on what you need. This is convenient.

## Monitoring

It monitors itself:
- Agent health
- Grant pipeline status
- System resources
- Community impact
- Learning progress

You can check these if you want. Or not.

## Deployment Options

You can run it three ways:

**Development Mode**: You can see everything it's doing. Good for learning how it works.

**Production Mode**: It runs in the background. Logs everything. Doesn't bother you.

**Cloud Mode**: It runs on servers somewhere else. Scales automatically. Costs money.

Pick one.

## Success Metrics

It tracks these things:
- How many grants it finds
- How many applications get approved
- How engaged the community is
- How efficiently it uses resources
- How much the agents learn
- How well they coordinate

Numbers go up. That's supposed to mean things are working.

## The BMAD Thing

Someone integrated something called BMAD into this. BMAD stands for Breakthrough Method for Agile AI-Driven Development, which is a lot of words.

It's in the `.bmad` folder. There are agent definitions and story templates. Shoghi loads them automatically.

You can add your own if you want. Or not.

See `bmad_loader.py` if you care about the details.

## Future Plans

The platform will expand. It always expands. Soon it will handle:
- Multi-community coordination
- Cross-sector partnerships
- Real-time resource allocation
- Predictive needs analysis
- Automated compliance
- Volunteer ecosystem management

Whether this is good or bad remains to be seen.

## Contributing

If you want to add something:

1. Describe what you want in regular language
2. Let the platform create the agents to build it
3. Test it
4. Share what you learned

That's how things grow here.

## A Final Note

This program was built to help communities. Communities like Puna, where people take care of each other and need resources to do it well.

Grant writing shouldn't require a PhD in bureaucracy. Coordination shouldn't require a degree in project management. Communities should be able to describe what they need and get help making it happen.

That's what this is for.

It's just a tool. Tools don't solve problems by themselves. People solve problems. But good tools help.

This is a good tool.

Use it to coordinate positive change.

*

**Mahalo for using Shoghi.**

*

And so on.
