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
  RFC1321:
  RFC3230:
  RFC2119:
  RFC5789:
  RFC5843:
  RFC4648:
  RFC5234:
  RFC6454:
  RFC6585:
  RFC7230:
  RFC7231:
  RFC7233:
  RFC7405:
  RFC8174:
  UNIX:
    title: The Single UNIX Specification, Version 2 - 6 Vol Set for UNIX 98
    author:
      name: The Open Group
      ins: The Open Group
    date: 1997-02

informative:
  RFC2818:
  RFC5788:
  RFC6962:
  RFC7396:

--- abstract

This document defines the RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset header fields for HTTP, thus allowing
 the server to publish current request quotas and the client to shape its requests and avoid
 receiving a 429 Too Many Request response.

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

It is common that those headers are returned by HTTP intermediaries
such that API Gateways or Reverse Proxies.

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
  : The rate-limit mechanisms described here are not meant to support
    authorization or other kinds of access controls. On the other side
    authorized users could be granted a quota.

  Definition of a Throttling scope:
  : This specification does not cover the throttling scope,
    that may be the given resource-target, its parent path or the whole
    Origin [RFC6454] section 7.

  Enforcing specific response status code:
  : This specification does not cover the response status code
    that may be used in throttled replies.
    

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

A basic quota mechanisms can be implemented defining the number of allowable
requests in a given time window, eg. 10 requests per second. 

Quotas may be enforced on different basis (eg. per user, per IP, ..) and
at different levels. For example, an user may be allowed to issue:

- 10 requests per second;
- limited to 60 request per minute;
- limited to 1000 request per hour.

When quota is exceeded, servers usually do not service the request

Instead, they reply with a `4xx` http status code (eg. 429 or 403)
or adopt more aggresive policies like dropping connections.

Complex throttling policies involving different windows can be poorly
implemented by clients.

This specification provides a standard way to communicate
quota informations so that the client avoids running over quota.

This specification does not cover:

-  the scope of the request throttling,
   that may be the given request-target, its parent path or the whole Origin;
-  whether non 2xx responses contribute or not to reach the quota limits.

...

# Header Specifications

The following headers are defined

## RateLimit-Limit {#ratelimit-limit-header}

The `RateLimit-Limit` response header field indicates the maximum number of
requests that the client is allowed to make in the time window, before
the server throttles it.

The header value is

    RateLimit-Limit = "RateLimit-Limit" ":" OWS ratelimit-limit-value
    ratelimit-limit-value = rlimit [ ";" "delay" "=" delay-seconds]
    rlimit = 1*DIGIT
    delay-seconds = 1*DIGIT

A `RateLimit-Limit` header MAY contain a `delay-seconds` parameter 
defining the quota interval.

If `delay-seconds` is not specified, it should be communicated out-of-bound
(eg. in the documentation) or inferred by the value of `RateLimit-Reset`
at the moment of the reset.

Examples:

~~~
   RateLimit-Limit: 100
   RateLimit-Limit: 100; delay=10
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

The `RateLimit-Reset` response header field indicates either:

- the number of seconds to the quota resets;
- the timestamp when the quota resets.

The header value is:

    RateLimit-Reset = "RateLimit-Reset" ":" OWS ratelimit-remaining-value
    ratelimit-remaining-value = Retry-After
    
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
  RateLimit-Limit: 100; delay=60
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


# Security Considerations

## Throttling does not prevent clients from issuing requests

While this specification helps client to avoid
going over quota, it does not prevent them to 
make further requests.

## Information disclosure

While this specification does not mandate whether non 2xx requests
consume quota, if 401 and 403 responses count on quota
a malicious client could get traffic informations of another
user probing the endpoints.


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

4. Why don't support multiple quota limits?

   We could, if there's an agreement on that ;) eg

   ```
   RateLimit-Limit: 10; delay=1, 50; delay=60, 1000; delay=3600, 5000; delay=86400
   ```

5. Do we want to tie this spec to RFC 6585?

   [RFC6585] defines the `429` status code. We could dis-entangle this spec from that
   one and avoing any suggestion on how to manage over-quota request.

6. Why not support multiple quota remaining?

   While this might be of some value, my experience suggests that overly-complex quota implementations
   results in lower effectiveness of this policy. This spec allows the client to easily focusing on
   RateLimit-Remaining and RateLimit-Reset.

7. Can I use RateLimit-\* in throttled responses?
   Yes, you can.
