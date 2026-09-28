/*****************************************************************************
 * Copyright [2026]
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 *****************************************************************************/
#ifndef CPPSRC_STARQUANT_COMMON_FXMACRODATA_H_
#define CPPSRC_STARQUANT_COMMON_FXMACRODATA_H_

#include <functional>
#include <string>
#include <utility>
#include <vector>

namespace StarQuant {

class FxMacroDataClient {
 public:
    using QueryParams = std::vector<std::pair<std::string, std::string>>;
    using Headers = std::vector<std::pair<std::string, std::string>>;
    using Transport = std::function<std::string(const std::string& method,
                                                const std::string& url,
                                                const Headers& headers,
                                                const std::string& body)>;

    explicit FxMacroDataClient(std::string api_key = "",
                               std::string base_url = "https://api.fxmacrodata.com/v1",
                               Transport transport = nullptr);

    std::string dataCatalogue(const std::string& currency, QueryParams params = {}) const;
    std::string announcements(const std::string& currency,
                              const std::string& indicator,
                              QueryParams params = {}) const;
    std::string latestAnnouncements(const std::string& currency, QueryParams params = {}) const;
    std::string announcementChanges(QueryParams params = {}) const;
    std::string calendar(const std::string& currency, QueryParams params = {}) const;
    std::string predictions(const std::string& currency,
                            const std::string& indicator,
                            QueryParams params = {}) const;
    std::string forex(const std::string& base, const std::string& quote,
                      QueryParams params = {}) const;
    std::string cot(const std::string& currency, QueryParams params = {}) const;
    std::string commodity(const std::string& indicator, QueryParams params = {}) const;
    std::string commoditiesLatest(QueryParams params = {}) const;
    std::string curves(const std::string& currency, QueryParams params = {}) const;
    std::string curveProxies(const std::string& currency, QueryParams params = {}) const;
    std::string forwardCurves(const std::string& currency, QueryParams params = {}) const;
    std::string rateDifferentials(const std::string& base,
                                  const std::string& quote,
                                  QueryParams params = {}) const;
    std::string forwardDifferentials(const std::string& base,
                                     const std::string& quote,
                                     QueryParams params = {}) const;
    std::string marketSessions(QueryParams params = {}) const;
    std::string riskSentiment(QueryParams params = {}) const;
    std::string news(const std::string& currency, QueryParams params = {}) const;
    std::string pressReleases(const std::string& currency, QueryParams params = {}) const;
    std::string graphql(const std::string& query,
                        const std::string& variables_json = "{}") const;
    std::string request(const std::string& path,
                        QueryParams params = {},
                        std::string method = "GET",
                        std::string body = "") const;

    std::string buildUrl(const std::string& path, QueryParams params = {}) const;
    // X-API-Key header for the configured key; empty when no key is set.
    Headers buildHeaders() const;

 private:
    std::string api_key_;
    std::string base_url_;
    Transport transport_;

    std::string send(const std::string& method,
                     const std::string& path,
                     QueryParams params,
                     const std::string& body = "") const;
};

}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_COMMON_FXMACRODATA_H_
