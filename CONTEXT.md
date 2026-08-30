# Mike Phuket AI

Telegram guide for Phuket that answers tourist questions, surfaces Partner offers, and qualifies real-estate interest. Operators run the bot; Partner Users see Partner statistics.

## Language

**Partner**:
A local business whose offer Mike shows in Telegram (name, type, referral link). Not a person and not a dashboard login.
_Avoid_: vendor, advertiser, account

**Partner Dashboard**:
The separate site where a Partner User views statistics for the Current Partner. Not the Operator admin panel. v1 is Russian (more languages later) and is the only place Views and Referral Clicks are shown.
_Avoid_: admin, portal, partner admin

**Partner User**:
A person who signs in to the Partner Dashboard with email and password. Created by an Operator with at least one Partner Access in the same step; no self-signup. Password is set and reset by an Operator; no self-serve reset. Cannot sign in unless they have at least one Partner Access. Email is unique and must not be an Operator’s email. An Operator may delete them; Views and Referral Clicks stay on the Partner.
_Avoid_: Partner (that is the business), Operator, account, login

**Partner Access**:
The grant that lets a Partner User see a Partner’s statistics. An Operator creates it with the Partner User and may revoke it. Usual case is one Partner User and one Partner; one User may access several Partners, and several Users may access the same Partner.
_Avoid_: membership, role, permission (too generic)

**Current Partner**:
The Partner whose statistics a Partner User is looking at. With several Access grants they choose it via a switcher on the stats page; with one Access there is no switcher.
_Avoid_: Listed Partner, selected business, workspace

**Listed**:
Whether Mike currently shows this Partner to Tourists. An unlisted Partner is hidden from Tourists; Partner Users with Access still see it on the Dashboard.
_Avoid_: active (same idea as the Operator checkbox), enabled, Current Partner

**Tourist**:
A person chatting with Mike in Telegram. Distinct from Partner User and Operator.
_Avoid_: user (too broad), customer, client

**View**:
One showing of that Partner’s card in Telegram. If several Partners of the same type are shown in one reply, each card is a View for that Partner. A tap on a Partner Type is not a View.
_Avoid_: impression (same thing, prefer View), topic event, type tap

**Referral Click**:
One tap that opens that Partner’s offer through Mike (name link or CTA). Each tap counts. Taps on old messages that skip Mike are not counted. We do not add estimates to this number.
_Avoid_: estimated click, mixed total, conversion, visit

**Opened View**:
A View after which the same Tourist made at least one Referral Click for that Partner. The stats circle divides Views into Opened vs not.
_Avoid_: conversion, CTR (the ratio is not the entity)

**Last 30 days**:
The rolling 30-day window ending today. Shown on the Partner stats page next to all-time.
_Avoid_: last month, calendar month

**Operator**:
Phuket ProMax staff who run the bot from the admin panel, including creating Partner Users and granting Partner Access. Distinct from a Partner User.
_Avoid_: admin (the app), Partner
