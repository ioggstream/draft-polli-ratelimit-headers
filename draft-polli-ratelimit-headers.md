---
title: Rate-Limit Header Fields for HTTP
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
so that the client can throttle its requests
and prevent 4xx or 5xx responses.


## Rate-limiting and quotas {#rate-limiting}

Servers use quota mechanisms to avoid systems overload,
to ensure an equitable distribution of computational resources
or to enforce other policies - eg. monetization.

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
to implement more complex policies, where
the number of acceptable request and the time window
are computed dynamically.

## Current landscape of rate-limiting headers

To help clients throttling their requests, many servers expose
the counters used to evaluate quota policies via HTTP header fields.

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
   * a datetime, either `HTTP-date` [RFC7231] or {{?RFC3339}}

- different headers, with the same semantic, are used by different implementers:

  * X-RateLimit-Limit and X-Rate-Limit-Limit
  * X-RateLimit-Remaining and X-Rate-Limit-Remaining
  * X-RateLimit-Reset and X-Rate-Limit-Reset

Client applications interfacing with different servers may thus
need to process different headers,
or the very same application interface that sits behind different
reverse proxies may reply with different throttling headers.

## This proposal

This proposal defines syntax and semantics for the following header fields:

- `RateLimit-Limit`: containing the requests quota in the time window;
- `RateLimit-Reset`: containing the time remaining in the current window, specified in seconds or as a timestamp;
- `RateLimit-Remaining`: containing the remaining requests quota in the current window;

The behavior of `RateLimit-Reset` is compatible with the one of `Retry-After`.

The preferred syntax for `RateLimit-Reset` is the seconds notation respect to the timestamp one.

The header definition allows to describe complex policies, including the ones
using multiple and variable time windows or implementing concurrency limits.

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

The "delta-seconds" rule is defined in {{!RFC7234}} section 1.2.1.

# Expressing rate-limit policies

## Time window {#time-window}

Rate limit policies limit the number of acceptable requests in a given time window.

A time window is expressed in seconds, using the following syntax:

    time-window = delta-seconds

Subsecond precision is not supported.

## Request quota {#request-quota}

The request-quota is a value associated to the maximum number of requests
that the server is willing to accept
from one or more clients
on a given basis (originating IP, authenticated user, geographical, ..)
during a time-window as defined in {{time-window}}.

The `request-quota` syntax is the following:

    request-quota = rlimit
    rlimit = 1*DIGIT

The `request-quota` SHOULD match the maximum number of acceptable requests.

The `request-quota` MAY differ from the total number of acceptable requests
when weight mechanisms or other server policies are implemented.

Example: A server could

- count once requests like `/books/{id}`
- count twice search requests like `/books?author=Camilleri`

so that we have the following counters

~~~
GET /books/123                  ; request-quota=4, remaining: 3, status=200
GET /books?author=Camilleri     ; request-quota=4, remaining: 1, status=200
GET /books?author=Eco           ; request-quota=4, remaining: 0, status=429
~~~

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
the `request-quota` associated to the client
in the current time-window.

If the client exceeds that limit, it MAY not be served.

The header value is

    RateLimit-Limit = ratelimit-limit-value
    ratelimit-limit-value = rlimit | 1#ratelimit-limit-value-w
    ratelimit-limit-value-w = rlimit; "window" "=" time-window 

A `ratelimit-limit-value` MAY contain a `window` parameter 
containing the `time-window`.

If the `window` parameter is not specified, the `time-window` MUST either be:

- inferred by the value of `RateLimit-Reset` at the moment of the reset, or
- communicated out-of-bound (eg. in the documentation).

Policies using multiple quota limits MAY be returned using multiple
`ratelimit-limit-value-w` items.

Three examples of `RateLimit-Limit` use are below.

~~~
   RateLimit-Limit: 100
   RateLimit-Limit: 100; window=10
   RateLimit-Limit: 10; window=1, 50; window=60, 1000; window=3600, 5000; window=86400
~~~

## RateLimit-Remaining {#ratelimit-remaining-header}

The `RateLimit-Remaining` response header field indicates the remaining `request-quota` {{request-quota}}
associated to the client.

The header syntax is:

    RateLimit-Remaining = rlimit
    rlimit = 1*DIGIT


Clients MUST NOT assume that a positive `RateLimit-Remaining` value imply
any guarantee of being served.
A low `RateLimit-Remaining` value is like a yellow traffic-light: the red light
will arrive suddenly.


One example of `RateLimit-Remaining` use is below.

~~~
   RateLimit-Remaining: 50
~~~

## RateLimit-Reset {#ratelimit-reset-header}

The `RateLimit-Reset` response header field indicates either

- the number of seconds until the quota resets, or
- the timestamp when the quota resets.

The header value is:

    RateLimit-Reset = delta-seconds / HTTP-date

The `HTTP-date` format is defined in [RFC7231] appendix D.

The `RateLimit-Reset` value:

- SHOULD use the `delta-seconds` format;
- MAY use the `HTTP-date` format.

The `HTTP-date` format is NOT RECOMMENDED.

The preferred format is the `delta-seconds` one, because:

- it does not rely on clock synchronization and is resilient to clock skew between client and server;
- it does not require support for the `obs-date` format [RFC7231] section 7.1.1.1 used by `HTTP-date`;
- it mitigates the risk related to thundering herd when too many clients are serviced with the same timestamp.

    
Two examples of `RateLimit-Reset` use are below.

~~~
   RateLimit-Reset: 50                              ; preferred delta-seconds notation
   RateLimit-Reset: Tue, 15 Nov 1994 08:12:31 GMT   ; HTTP-date notation
~~~

The client MUST NOT give for granted that all its `request-quota` will be restored
after the moment referenced by `RateLimit-Reset`.
The server MAY arbitrarily alter the `RateLimit-Reset` value between subsequent requests
eg. in case of resource saturation or to implement sliding window policies.



# Providing Rate-Limit headers

A server MAY use one or more `RateLimit` response header fields
defined in this document to communicate its quota policies.

The returned values apply to the metrics used to evaluate the quota policy
respect to the current request and MAY not apply to subsequent requests.

Example: a successful response with the following header fields

    RateLimit-Limit: 10
    RateLimit-Remaining: 1
    RateLimit-Reset: 7

does not imply that the next request will always be successful. Server metrics may be subject to other
conditions like the one shown in the example from {{request-quota}}.

A server MAY return `RateLimit` response header fields independently
of the response status code.  This includes throttled responses.

If a response contains both the `Retry-After` and the `RateLimit-Reset` header fields,
the value of `RateLimit-Reset` MUST be consistent with the one of `Retry-After`.

When using a quota policy involving more than one time-window,
the server MUST reply with the `RateLimit` headers related to the window
with the lower `RateLimit-Remaining` values.

Under certain conditions, a server MAY artificially lower `RateLimit` headers values between subsequent requests,
eg. to respond to Denial of Service attacks or in case of resource saturation.


# Receiving Rate-Limit headers

A client MUST process the received `RateLimit` headers.

`RateLimit` headers with malformed values MAY be ignored.

A client SHOULD NOT exceed the request-quota expressed in `RateLimit-Remaining` before the `time-window` expressed
in `RateLimit-Reset`.

A client MUST validate the values received in the `RateLimit` headers before using them
and check if there are significant discrepancies
with the expected ones.
This includes a `RateLimit-Reset` moment too far in the future or a `request-quota` too high.

If a response contains both the `RateLimit-Remaining` and `Retry-After` header fields,
the `Retry-After` header field MUST take precedence and
the `RateLimit-Remaining` header field MAY be ignored.

# Examples

## Unparameterized responses

### Throttling informations in responses

The client is allowed to make 99 more requests in the next 50 seconds.
The `time-window` is communicated out-of-bound or inferred by the header values.

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

### Use in conjunction with custom headers {#use-with-custom-headers}

The server uses two custom headers,
namely `acme-RateLimit-DayLimit` and `acme-RateLimit-HourLimit`
to expose the following policy:

- 5000 daily request-quota;
- 1000 hourly request-quota.

The client consumed 4900 request-quota in the first 14 hours.

Despite the next hourly limit of 1000 request-quota, the closest limit
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
per minute,
and in case of resource exhaustion adapts the returned values
reducing both `RateLimit-Limit` and `RateLimit-Remaining`.

After 2 seconds the server replied to 40 requests

~~~
Request:

  GET /items/123

Response:

  HTTP/1.1 200 Ok
  Content-Type: application/json
  RateLimit-Limit: 100
  RateLimit-Remaining: 60
  RateLimit-Reset: 58

  {"elapsed": 2, "issued": 40}
~~~

At the subsequent 41th request - due to resource exhaustion -
the server advertises only `RateLimit-Remaining: 20`.

~~~
Request:

  GET /items/123

Response:

  HTTP/1.1 200 Ok
  Content-Type: application/json
  RateLimit-Limit: 100
  RateLimit-Remaining: 20
  RateLimit-Reset: 56

  {"elapsed": 4, "issued": 41}
~~~


### Use in throttled responses

A client exhausted its quota and the server throttles the request
sending the `Retry-After` response header field.

The values of `Retry-After` and `RateLimit-Reset` are consistent as they
reference the same moment.

The `429 Too Many Requests` HTTP status code is just used as an example.

~~~
Request:

  GET /items/123

Response:

  HTTP/1.1 429 Too Many Requests
  Content-Type: application/json
  Date: Mon, 05 Aug 2019 09:27:00 GMT
  Retry-After: Mon, 05 Aug 2019 09:27:05 GMT
  RateLimit-Reset: 5
  RateLimit-Limit: 100
  Ratelimit-Remaining: 0

  {
    "title": "Too Many Requests",
    "status": 429,
    "detail": "You have exceeded your quota"
  }
~~~


## Parameterized responses

### Throttling window specified via parameter

The client is allowed to make 99 more requests in the next 50 seconds.
The `time-window` is communicated by the `window` parameter, so we know the quota is 100 requests
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

The server does not expose `RateLimit-Remaining` values, but
resets the limit counter every second.

It communicates to the client the limit of 10 request per second
always returning the couple `RateLimit-Limit` and `RateLimit-Reset`.

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

This is a standardized way of describing the policy
detailed in {{use-with-custom-headers}}:

- 5000 daily request-quota;
- 1000 hourly request-quota.

The client consumed 4900 request-quota in the first 14 hours.

Despite the next hourly limit of 1000 request-quota, the closest limit
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

## Remaining requests are not granted requests

The values passed in `RateLimit-*` headers are hints given from the server
to the clients in order to avoid being throttled out.

Clients MUST NOT give for granted the values returned in `RateLimit-Remaining`.

In case of resource saturation, the server MAY artificially lower the returned
values or not serve the request anyway.

## Reliability of RateLimit-Reset

Consider that `request-quota` may not be restored after the moment referenced by `RateLimit-Reset`,
and the `RateLimit-Reset` value should not be considered fixed nor constant.

Subsequent requests may return an increased value of `RateLimit-Reset` to limit
concurrency or implement dynamic or adaptive throttling policies.

## Resource exhaustion and clock skew

When returning `RateLimit-Reset`, implementers must be aware that many throttled
clients may come back at the very moment specified. For example, if the time-window
is one hour and the returned value is something like

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

2. Why using delta-seconds instead of UNIX Timestamp? Why HTTP-date is NOT RECOMMENDED?

   Using delta-seconds permits to align with Retry-After header, which is returned in similar contexts,
   eg on 429 responses.

   delta-seconds as defined in [RFC7234] section 1.2.1 clarifies some parsing rules too.

   As explained in [RFC7231] section 4.1.1.1 using HTTP-date requires the use of a clock synchronization
   protocol. This may be problematic (eg. clock skew, failure of hardcoded clock synchronization servers,
   IoT devices, ..).

3. Why don't pass the trottling scope as a parameter?

   We could if there's an agreement on that ;).

4. Do `RateLimit-Limit` and `RateLimit-Remaining` represent the exact number of requests
   I can issue?

   No, unless there's agreement on that.
   As servers may weight requests, this to not impose a 1-1 mapping between
   the "requests quota" and the "maximum number of requests".
   For example a server can:

   - count once requests like `/books/{id}`
   - count twice search requests like `/books?author=Camilleri`

5. Do we want to tie this spec to RFC 6585?

   [RFC6585] defines the `429` status code. We could dis-entangle this spec from that
   one and avoiding any suggestion on which HTTP status code to use in over-quota request.

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

9. Do a positive value of `RateLimit-Remaining` imply any service guarantee for my
   future requests to be served?

   No. The returned values were used to decide whether to serve or not *the current request*
   and so they do not imply any guarantee that future requests will be successful.

   Instead they provide informations that should be used to understand when future requests
   have an high probablility of not being successful. A low value for `RateLimit-Remaining`
   should be intepreted as a yellow traffic-light instead of a green one.

   Servers implementing sliding window techniques or concurrency limits moreover may arbitrarily
   lower the internal counters used to compute the remaining quota values.
