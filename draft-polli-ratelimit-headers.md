---
title: Rate-Limit headers for HTTP
abbrev:
docname: draft-polli-ratelimit-headers-latest
category: std

ipr: trust200902
area: General
workgroup:
keyword: Internet-Draft

stand_alone: yes
pi: [toc, tocindent, sortrefs, symrefs, strict, compact, comments, inline, docmapping]

author:
 -
    ins: R. Polli
    name: Roberto Polli
    org: Team Digitale, Italian Government
    email: robipolli@gmail.com

normative:
  RFC2119:
  RFC5234:
  RFC6454:
  RFC7230:
  RFC7231:
  RFC7405:
  RFC8174:
  UNIX:
    title: The Single UNIX Specification, Version 2 - 6 Vol Set for UNIX 98
    author:
      name: The Open Group
      ins: The Open Group
    date: 1997-02

informative:
  RFC6585:

--- abstract

This document defines the RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset header fields for HTTP,
thus allowing servers to publish current request quotas and
clients to shape their request policy and avoid being throttled out.

--- note_Note_to_Readers

*RFC EDITOR: please remove this section before publication*

Discussion of this draft takes place on the HTTP working group mailing list
(ietf-http-wg@w3.org), which is archived at
<https://lists.w3.org/Archives/Public/ietf-http-wg/>.

The source code and issues list for this draft can be found at
<https://github.com/ioggstream/draft-polli-ratelimit-headers>.


--- middle

# Introduction

The widespreading of HTTP as a distributed computation protocol
requires an explicit way of communicating service status and
usage quotas.

This was partially addressed with the `Retry-After` header field
defined in [RFC7231] to be returned in `429 Too Many Requests` or 
`503 Service Unavailable` responses.

Still, there is not a standard way to communicate service quotas
in a way to prevent 4xx or 5xx responses, so that 
the client can throttle its requests. 


## Current landscape of rate-limiting headers

On the web we can find many different rate-limit headers, usually
containing the number of allowed requests
in a given time window, and when the window is reset.

The common choice is to return three headers containing:

- the maximum number of allowed requests in the time window;
- the number of remaining requests in the current window;
- the time remaining in the current window expressed in seconds or 
  as a timestamp;

Those response headers may be added by HTTP intermediaries
such as API gateways and reverse proxies.

Almost all rate-limit headers implementations do not use subsecond precision,
because the conveyed values are usually subject to response-time latency.

Commonly used header field names are:

- `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`; 
- `X-Rate-Limit-Limit`, `X-Rate-Limit-Remaining`, `X-Rate-Limit-Reset`.

There are variants too, where the window is specified
in the header field name, eg:

- `x-ratelimit-limit-minute`, `x-ratelimit-limit-hour`, `x-ratelimit-limit-day`
- `x-ratelimit-remaining-minute`, `x-ratelimit-remaining-hour`, `x-ratelimit-remaining-day`

### Interoperability issues

A major interoperability issue in throttling is the lack
of standard headers, because:

- each implementation associates different semantics to the
  same header field names;
- header field names proliferates.

Here are some examples:

- `X-RateLimit-Remaining` references different values, depending on the implementation:

   * seconds remaining to the window expiration
   * milliseconds remaining to the window expiration
   * seconds since UTC, in UNIX Timestamp
   * a datetime, either HTTP-Date or {{?RFC3339}}

- different headers, with the same semantic, are used by different implementors:

  * X-RateLimit-Limit and X-Rate-Limit-Limit
  * X-RateLimit-Remaining and X-Rate-Limit-Remaining
  * X-RateLimit-Reset and X-Rate-Limit-Reset

Client applications interfacing with different servers may thus
need to process different headers,
or the very same application interface that sits behind different 
reverse proxies may reply with different throttling headers.

## This proposal

This proposal defines syntax and semantics for the following throttling header fields:

- `RateLimit-Limit`: containing the maximum number of allowed requests in the time window;
- `RateLimit-Reset`: containing the time remaining in the current window, specified in seconds or as a timestamp;
- `RateLimit-Remaining`: containing the number of remaining requests in the current window;

The behavior of `RateLimit-Reset` is compatible with the one of `Retry-After`.

To mitigate issues related to clock synchronization, the preferred way to
specify the `RateLimit-Reset` is using the seconds notation respect to the timestamp one.

## Goals

The goals of this proposal are:

   1. Standardizing the names and semantic of rate-limit headers;

   2. Improve resiliency of HTTP infrastructures simplifying
      the enforcement and the adoption of rate-limit headers;

   3. Simplify API documentation avoiding expliciting
      rate-limit header fields semantic in documentation.

The goals do not include:

  Authorization:
  : The rate-limit headers described here are not meant to support
    authorization or other kinds of access controls.

  Throttling scope:
  : This specification does not cover the throttling scope,
    that may be the given resource-target, its parent path or the whole
    Origin [RFC6454] section 7.

  Response status code:
  : This specification does not cover the response status code
    that may be used in throttled responses, nor ties the rate-limit
    headers to any HTTP status code. They may be returned in both
    Successful and non Successful responses.
    Moreover this specification does not cover whether non Successful
    responses count on quota usage.

  Throttling policy:
  : This specification does not impose any throttling policy, but
    provides a mechanism for communicating quota metrics.
    The values published in the headers, including the window size,
    can be statically or dynamically evaluated.
    Moreover a different weight may be assigned to different requests.

  Service Level Agreement:
  : This specification allows a server to provide quota hints to the clients.
    Those hints do not imply that respectful clients will not be throttled
    out or denied service under certain circumstances.


## Notational Conventions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in BCP 14 ([RFC2119] and [RFC8174])
when, and only when, they appear in all capitals, as shown here.

This document uses the Augmented BNF defined in [RFC5234] and updated
by [RFC7405] along with the "#rule" extension defined in Section 7 of
[RFC7230].

The term Origin is to be interpreted as described in [RFC6454] section 7.

# Throttling requests {#throttling}

Servers use quota mechanisms to avoid systems overload, 
to ensure an equitable distribution of computational resources 
or to enforce other policies - eg monetization.

A basic quota mechanism limits the number of acceptable
requests in a given time window, eg. 10 requests per second.

When quota is exceeded, servers usually do not serve the request
replying instead with a `4xx` HTTP status code (eg. 429 or 403)
or adopt more aggressive policies like dropping connections.

Quotas may be enforced on different basis (eg. per user, per IP, per geographic area, ..) and
at different levels. For example, an user may be allowed to issue:

- 10 requests per second;
- limited to 60 request per minute;
- limited to 1000 request per hour.

Moreover system metrics, statistics and heuristics can be used
to implement dynamic and more complex policies.

Complex throttling policies involving different windows and related header
field names can be poorly implemented by clients.

This specification provides a standard way to communicate
quota informations to help clients avoiding running over quota.

## Time window {#time-window}

Rate limit policies allow a client to issue a maximum number
of requests in a give time window.

The `time-window` value is in seconds, and its syntax is the following:

    time-window = delay-seconds
    delay-seconds = 1*DIGIT

Subsecond precision is not supported.

## Further considerations

This specification does not cover:

-  the scope of the request throttling,
   that may be the given request-target, its parent path or the whole Origin;
-  whether non 2xx responses contribute or not to reach the quota limits;
-  which strategies to use to implement your quota policy.

...

# Header Specifications

The following `RateLimit` response header fields are defined

Note: RFC EDITOR PLEASE DELETE THIS NOTE; Implementations of drafts
of this specification MUST NOT use the `RateLimit` prefix. Instead
they MUST use the `X-RateLimit` one. Draft header field names
are thus `X-RateLimit-Limit`, `X-RateLimit-Remaining` and `X-RateLimit-Reset`.

## RateLimit-Limit {#ratelimit-limit-header}

The `RateLimit-Limit` response header field indicates
the maximum number of requests that the server allocated to the client
in the current time-window.

If the client exceeds that limit, it MAY not be served.

The header value is

    RateLimit-Limit = "RateLimit-Limit" ":" OWS ratelimit-limit-value
    ratelimit-limit-value = rlimit | 1#ratelimit-limit-value-w
    ratelimit-limit-value-w = rlimit; "window" "=" time-window 
    rlimit = 1*DIGIT

A `ratelimit-limit-value` MAY contain a `window` parameter 
defining the {#time-window} interval.

If the `window` parameter is not specified, the {#time-window} MUST either:

- inferred by the value of `RateLimit-Reset` at the moment of the reset;
- be communicated out-of-bound (eg. in the documentation).

Quota policies using multiple quota limits MAY be returned using multiple
`ratelimit-limit-value-w` items.

Examples:

~~~
   RateLimit-Limit: 100
   RateLimit-Limit: 100; window=10
   RateLimit-Limit: 10; window=1, 50; window=60, 1000; window=3600, 5000; window=86400
~~~

## RateLimit-Remaining {#ratelimit-remaining-header}

The `RateLimit-Remaining` response header field indicates the number of
requests left the client until the quota resets.

The header value is

    RateLimit-Remaining = "RateLimit-Remaining" ":" OWS ratelimit-remaining-value
    ratelimit-remaining-value = rlimit
    rlimit = 1*DIGIT
    
Examples:

~~~
   RateLimit-Remaining: 50
~~~

## RateLimit-Reset {#ratelimit-reset-header}

The `RateLimit-Reset` response header field indicates either

- the number of seconds until the quota resets, or
- the timestamp when the quota resets.

The header value is:

    RateLimit-Reset = "RateLimit-Reset" ":" OWS ratelimit-reset-value
    ratelimit-reset-value = Retry-After
    
The value of `Retry-After` is defined in [RFC7231] appendix D and:

- it SHOULD be number of seconds to delay after the quota is exhausted;
- it CAN be an HTTP-date.

The preferred way is to expose the number of seconds to delay to mitigate
the risk of clock skew between client and server, and potential issues
of thundering herd when too many clients are serviced with the same timestamp.

    
Examples:

~~~
   RateLimit-Reset: 50
   RateLimit-Reset: Tue, 15 Nov 1994 08:12:31 GMT

~~~

# Providing Rate-Limit headers

A server MAY use one or more of the Rate-Limit response header fields
defined in this document to communicate its quota policies.

When using a quota policy involving more than one window,
the server MUST reply with the `RateLimit` headers related to the window
with the lower `RateLimit-Remaining` values.

Under certain conditions, a server MAY artificially lower RateLimit headers values,
eg to respond to Denial of Service attacks or in case of resource saturation.

Clients MUST NOT assume that respecting `RateLimit` headers values imply any
guarantee of being served.



# Examples

## Unparameterized responses

### Throttling informations in responses

The client is allowed to make 99 more requests in the next 50 seconds.
Throttling interval is communicated out-of-bound.

~~~
Request:

  GET /items/123

Response:

  HTTP/1.1 200 Ok
  Content-Type: application/json
  RateLimit-Limit: 100
  Ratelimit-Remaining: 99
  Ratelimit-Reset: 50

  {"hello": "world"}
~~~

### Throttling window specified via parameter

The client is allowed to make 99 more requests in the next 50 seconds.
Throttling interval is communicated by `delay`, so we know the quota is 100 requests
per minute.

~~~
Request:

  GET /items/123

Response:

  HTTP/1.1 200 Ok
  Content-Type: application/json
  RateLimit-Limit: 100; window=60
  Ratelimit-Remaining: 99
  Ratelimit-Reset: 50

  {"hello": "world"}
~~~


### Missing Remaining informations

The server does not expose `RateLimit-Remaining` informations, but
resets the limit counter every second, and always returns the couple
`RateLimit-Limit` and `RateLimit-Reset` expliciting that the client
should respect 10 request per second.

~~~
Request:

  GET /items/123

Response:

  HTTP/1.1 200 Ok
  Content-Type: application/json
  RateLimit-Limit: 10
  Ratelimit-Reset: 1

  {"first": "request"}
~~~

~~~
Request:

  GET /items/123

Response:

  HTTP/1.1 200 Ok
  Content-Type: application/json
  RateLimit-Limit: 10
  Ratelimit-Reset: 1

  {"second": "request"}
~~~

### Use with multiple windows

Daily quota is 5000, and the client consumed 4900
in the first 5 hours.
Despite of the next hourly limit, the closest limit
to reach is the daily one.

The server then exposes the `RateLimit` headers to
inform the client that:

- it has only 100 request left;
- the window will reset in 10 hours.

~~~
Request:

  GET /items/123

Response:

  HTTP/1.1 200 Ok
  Content-Type: application/json
  RateLimit-Limit: 1000; window=3600, 5000; window=86400
  RateLimit-Remaining: 100
  RateLimit-Reset: 36000

  {"hello": "world"}
~~~

### Use in conjunction with custom headers

The server uses two custom headers, 
namely `acme-RateLimit-DayLimit` and `acme-RateLimit-HourLimit`
to expose the quotas.

Daily quota is 5000, and the client consumed 4900
in the first 5 hours.  Despite of the next hourly limit, the closest limit
to reach is the daily one.

The server then exposes the `RateLimit-*` headers to
inform the client that:

- it has only 100 request left;
- the window will reset in 10 hours.

~~~
Request:

  GET /items/123

Response:

  HTTP/1.1 200 Ok
  Content-Type: application/json
  acme-RateLimit-DayLimit: 5000
  acme-RateLimit-HourLimit: 1000
  RateLimit-Limit: 5000
  RateLimit-Remaining: 100
  RateLimit-Reset: 36000

  {"hello": "world"}
~~~


### Use for limiting concurrency

Throttling headers may be used to limit concurrency,
advertising limits that are lower than the usual ones
in case of saturation, thus increasing availability.

The server adopted a basic quota policy of 100 requests
per minute. For clarity we added the window parameter.

Due to resource exhaustion, it implemented a policy that
adapt the values returned in the rate-limit headers,
reducing both RateLimit-Limit and RateLimit-Remaining.


~~~
Request:

  GET /items/123

Response:

  HTTP/1.1 200 Ok
  Content-Type: application/json
  RateLimit-Limit: 50; window=60
  RateLimit-Remaining: 20
  RateLimit-Reset: 58

  {"hello": "world"}
~~~

# Security Considerations

## Throttling does not prevent clients from issuing requests

While this specification helps clients to avoid
going over quota, it does not prevent them to 
make further requests.

Servers should always implement their mechanisms
to prevent resource exhaustion.

## Information disclosure

While this specification does not mandate whether non 2xx requests
consume quota, if 401 and 403 responses count on quota
a malicious client could get traffic informations of another
user probing the endpoints.

## Remainig requests are not granted requests

The values passed in `Rate-Limit-*` headers are hints given from the server
to the clients in order to avoid being throttled out.

Clients SHOULD NOT give for granted the values returned in `RateLimit-Remaining`.

In case of resource saturation, the server MAY artificially lower the returned
values or not serve the request anyway.

## Resource exhaustion and clock skew

When returning `RateLimit-Reset`, implementors must be aware that many throttled
clients may come back at the very moment specified. For example, if the throttling
interval is hourly and the retured value is something like

```
RateLimit-Reset: Tue, 15 Nov 1994 08:00:00 GMT
```

there's a high probability that all clients will show up at `08:00:00`.

This could be mitigated adding some jitter to the header value. 

...

# IANA Considerations


## RateLimit-Limit Header Field Registration

This section registers the `RateLimit-Limit` header field in the "Permanent Message
Header Field Names" registry ({{!RFC3864}}).

Header field name:  `RateLimit-Limit`

Applicable protocol:  http

Status:  standard

Author/Change controller:  IETF

Specification document(s):  {{ratelimit-limit-header}} of this document

## RateLimit-Remaining Header Field Registration

This section registers the `RateLimit-Remaining` header field in the "Permanent Message
Header Field Names" registry ({{!RFC3864}}).

Header field name:  `RateLimit-Remaining`

Applicable protocol:  http

Status:  standard

Author/Change controller:  IETF

Specification document(s):  {{ratelimit-remaining-header}} of this document

## RateLimit-Reset Header Field Registration

This section registers the `RateLimit-Reset` header field in the "Permanent Message
Header Field Names" registry ({{!RFC3864}}).

Header field name:  `RateLimit-Reset`

Applicable protocol:  http

Status:  standard

Author/Change controller:  IETF

Specification document(s):  {{ratelimit-reset-header}} of this document


--- back

# Change Log

RFC EDITOR PLEASE DELETE THIS SECTION.


# Acknowledgements

TBD


# FAQ

1. Why defining standard headers for throttling?

   To simplify enforcement of throttling policies.

2. Why using delay-seconds instead of UNIX Timestamp?

   To align with Retry-After header, which is returned in similar contexts, eg on 429 responses.

3. Why don't pass the trottling scope as a parameter?

   We could if there's an agreement on that ;).


5. Do we want to tie this spec to RFC 6585?

   [RFC6585] defines the `429` status code. We could dis-entangle this spec from that
   one and avoing any suggestion on how to manage over-quota request.

6. Why not support multiple quota remaining?

   While this might be of some value, my experience suggests that overly-complex quota implementations
   results in lower effectiveness of this policy. This spec allows the client to easily focusing on
   RateLimit-Remaining and RateLimit-Reset.

7. Can I use RateLimit-\* in throttled responses (eg together with 429)?
   Yes, you can.

8. Shouldn't I limit concurrency instead of request rate?
   You can do both. The goal of this spec is to provide guidance for
   clients in shaping their requests without being throttled out.

   Usually, limiting concurrency results in unserviced client requests,
   which is something you may want to avoid.

   A standard way to limit concurrency is to return 503 + Retry-After
   in case of resource saturation (eg. thrashing, connection queues too long,
   Service Level Objectives not meet, ..).

   Dynamically lowering the values returned by the rate-limit headers,
   and returning retry-after along with them can improve availability.

   Saturation conditions can be either dynamic or static: all this is out of
   the scope for the current document.

