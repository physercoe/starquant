/*****************************************************************************
 * Copyright [2026]
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 *****************************************************************************/

#include <Common/fxmacrodata.h>

#include <cctype>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace StarQuant {
namespace {

std::string trimTrailingSlash(std::string value) {
    while (!value.empty() && value.back() == '/') {
        value.pop_back();
    }
    return value;
}

std::string ensureLeadingSlash(const std::string& path) {
    if (!path.empty() && path.front() == '/') {
        return path;
    }
    return "/" + path;
}

std::string lower(std::string value) {
    for (char& ch : value) {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }
    return value;
}

std::string encode(const std::string& value) {
    std::ostringstream out;
    out << std::uppercase << std::hex;
    for (unsigned char ch : value) {
        if (std::isalnum(ch) || ch == '-' || ch == '_' || ch == '.' || ch == '~') {
            out << static_cast<char>(ch);
        } else {
            out << '%' << std::setw(2) << std::setfill('0') << static_cast<int>(ch);
        }
    }
    return out.str();
}

}  // namespace

FxMacroDataClient::FxMacroDataClient(std::string api_key,
                                     std::string base_url,
                                     Transport transport)
    : api_key_(std::move(api_key)),
      base_url_(trimTrailingSlash(std::move(base_url))),
      transport_(std::move(transport)) {}

std::string FxMacroDataClient::buildUrl(const std::string& path, QueryParams params) const {
    std::ostringstream url;
    url << base_url_ << ensureLeadingSlash(path);
    char separator = '?';
    for (const auto& param : params) {
        url << separator << encode(param.first) << '=' << encode(param.second);
        separator = '&';
    }
    return url.str();
}

FxMacroDataClient::Headers FxMacroDataClient::buildHeaders() const {
    Headers headers;
    if (!api_key_.empty()) {
        headers.push_back({"X-API-Key", api_key_});
    }
    return headers;
}

std::string FxMacroDataClient::send(const std::string& method,
                                    const std::string& path,
                                    QueryParams params,
                                    const std::string& body) const {
    if (!transport_) {
        throw std::runtime_error("FxMacroDataClient requires a transport callback");
    }
    return transport_(method, buildUrl(path, std::move(params)), buildHeaders(), body);
}

std::string FxMacroDataClient::dataCatalogue(const std::string& currency,
                                             QueryParams params) const {
    return send("GET", "/data_catalogue/" + encode(lower(currency)), std::move(params));
}

std::string FxMacroDataClient::announcements(const std::string& currency,
                                             const std::string& indicator,
                                             QueryParams params) const {
    return send("GET", "/announcements/" + encode(lower(currency)) + "/" + encode(indicator),
                std::move(params));
}

std::string FxMacroDataClient::latestAnnouncements(const std::string& currency,
                                                   QueryParams params) const {
    return send("GET", "/announcements/" + encode(lower(currency)) + "/latest",
                std::move(params));
}

std::string FxMacroDataClient::announcementChanges(QueryParams params) const {
    return send("GET", "/announcements/changes", std::move(params));
}

std::string FxMacroDataClient::calendar(const std::string& currency,
                                        QueryParams params) const {
    return send("GET", "/calendar/" + encode(lower(currency)), std::move(params));
}

std::string FxMacroDataClient::predictions(const std::string& currency,
                                           const std::string& indicator,
                                           QueryParams params) const {
    return send("GET", "/predictions/" + encode(lower(currency)) + "/" + encode(indicator),
                std::move(params));
}

std::string FxMacroDataClient::forex(const std::string& base,
                                     const std::string& quote,
                                     QueryParams params) const {
    return send("GET", "/forex/" + encode(lower(base)) + "/" + encode(lower(quote)),
                std::move(params));
}

std::string FxMacroDataClient::cot(const std::string& currency,
                                   QueryParams params) const {
    return send("GET", "/cot/" + encode(lower(currency)), std::move(params));
}

std::string FxMacroDataClient::commodity(const std::string& indicator,
                                         QueryParams params) const {
    return send("GET", "/commodities/" + encode(indicator), std::move(params));
}

std::string FxMacroDataClient::commoditiesLatest(QueryParams params) const {
    return send("GET", "/commodities/latest", std::move(params));
}

std::string FxMacroDataClient::curves(const std::string& currency,
                                      QueryParams params) const {
    return send("GET", "/curves/" + encode(lower(currency)), std::move(params));
}

std::string FxMacroDataClient::curveProxies(const std::string& currency,
                                            QueryParams params) const {
    return send("GET", "/curve_proxies/" + encode(lower(currency)), std::move(params));
}

std::string FxMacroDataClient::forwardCurves(const std::string& currency,
                                             QueryParams params) const {
    return send("GET", "/forward_curves/" + encode(lower(currency)), std::move(params));
}

std::string FxMacroDataClient::rateDifferentials(const std::string& base,
                                                 const std::string& quote,
                                                 QueryParams params) const {
    return send("GET", "/rate_differentials/" + encode(lower(base)) + "/" + encode(lower(quote)),
                std::move(params));
}

std::string FxMacroDataClient::forwardDifferentials(const std::string& base,
                                                    const std::string& quote,
                                                    QueryParams params) const {
    return send("GET", "/forward_differentials/" + encode(lower(base)) + "/" + encode(lower(quote)),
                std::move(params));
}

std::string FxMacroDataClient::marketSessions(QueryParams params) const {
    return send("GET", "/market_sessions", std::move(params));
}

std::string FxMacroDataClient::riskSentiment(QueryParams params) const {
    return send("GET", "/risk_sentiment", std::move(params));
}

std::string FxMacroDataClient::news(const std::string& currency,
                                    QueryParams params) const {
    return send("GET", "/news/" + encode(lower(currency)), std::move(params));
}

std::string FxMacroDataClient::pressReleases(const std::string& currency,
                                             QueryParams params) const {
    return send("GET", "/press-releases/" + encode(lower(currency)), std::move(params));
}

std::string FxMacroDataClient::graphql(const std::string& query,
                                       const std::string& variables_json) const {
    return send("POST", "/graphql", {},
                "{\"query\":\"" + query + "\",\"variables\":" + variables_json + "}");
}

std::string FxMacroDataClient::request(const std::string& path,
                                       QueryParams params,
                                       std::string method,
                                       std::string body) const {
    return send(std::move(method), path, std::move(params), body);
}

}  // namespace StarQuant
