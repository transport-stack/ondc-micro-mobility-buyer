CACHE_DELIMITER = "buyer"
CACHE_TIMEOUT = 900
TIMESTAMP_CACHE_TIMEOUT = 60
DISCOUNT = 0.9
PASSENGER_COUNT = 1
CHARTR_GENERIC_USER_NAME = "One Delhi app user"


class AutoRideState:
    RIDE_ASSIGNED = "RIDE_ASSIGNED"
    RIDE_STARTED = "RIDE_STARTED"
    RIDE_ENROUTE_PICKUP = "RIDE_ENROUTE_PICKUP"
    RIDE_ARRIVED_PICKUP = "RIDE_ARRIVED_PICKUP"
    RIDE_ENDED = "RIDE_ENDED"


class AutoRideStatus:
    ACTIVE = "ACTIVE"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"


payments_tags_array = [
                    {
                        "descriptor": {"code": "BUYER_FINDER_FEES"},
                        "display": False,
                        "list": [
                            {"descriptor": {"code": "BUYER_FINDER_FEES_PERCENTAGE"}, "value": "0"},
                            {"descriptor": {"code": "BUYER_FINDER_FEES_TYPE"}, "value": "percent-annualized"}
                        ]
                    },
                    {
                        "descriptor": {
                            "code": "SETTLEMENT_TERMS"
                        },
                        "display": False,
                        "list": [
                            {
                                "descriptor": {
                                    "code": "SETTLEMENT_WINDOW"
                                },
                                "value": "PT60M"
                            },
                            {
                                "descriptor": {
                                    "code": "SETTLEMENT_BASIS"
                                },
                                "value": "Delivery"
                            },
                            {
                                "descriptor": {
                                    "code": "SETTLEMENT_TYPE"
                                },
                                "value": "upi"
                            },
                            {
                                "descriptor": {
                                    "code": "MANDATORY_ARBITRATION"
                                },
                                "value": "true"
                            },
                            {
                                "descriptor": {
                                    "code": "COURT_JURISDICTION"
                                },
                                "value": "New Delhi"
                            },
                            {
                                "descriptor": {
                                    "code": "DELAY_INTEREST"
                                },
                                "value": "2.5"
                            },
                            {
                                "descriptor": {
                                    "code": "STATIC_TERMS"
                                },
                                "value": "https://www.abc.com/settlement-terms/"
                            },
                            {
                                "descriptor": {
                                    "code": "SETTLEMENT_AMOUNT"
                                },
                                "value": ""
                            }
                        ]
                    }
                ]

billing = {
        "name": "Chartr"
      }


init_settlement_data = {
                      "collected_by": "BPP",
                      "params": {
                        "bank_account_number": "xxxxxxxxxxxxxx",
                        "bank_code": "XXXXXXXX",
                      },
                      "status": "NOT-PAID",
                      "tags": [
                        {
                          "descriptor": {
                            "code": "BUYER_FINDER_FEES"
                          },
                          "display": False,
                          "list": [
                            {
                              "descriptor": {
                                "code": "BUYER_FINDER_FEES_PERCENTAGE"
                              },
                              "value": "0"
                            }
                          ]
                        },
                        {
                          "descriptor": {
                            "code": "SETTLEMENT_TERMS"
                          },
                          "display": False,
                          "list": [
                            {
                              "descriptor": {
                                "code": "SETTLEMENT_WINDOW"
                              },
                              "value": "PT60M"
                            },
                            {
                              "descriptor": {
                                "code": "SETTLEMENT_BASIS"
                              },
                              "value": "DELIVERY"
                            },
                            {
                              "descriptor": {
                                "code": "SETTLEMENT_TYPE"
                              },
                              "value": "UPI"
                            },
                            {
                              "descriptor": {
                                "code": "MANDATORY_ARBITRATION"
                              },
                              "value": "true"
                            },
                            {
                              "descriptor": {
                                "code": "COURT_JURISDICTION"
                              },
                              "value": "New Delhi"
                            },
                            {
                              "descriptor": {
                                "code": "DELAY_INTEREST"
                              },
                              "value": "0"
                            },
                            {
                              "descriptor": {
                                "code": "STATIC_TERMS"
                              },
                              "value": "https://example-test-bpp.com/static-terms.txt"
                            }
                          ]
                        }
                      ],
                      "type": "ON-FULFILLMENT"
                    }


confirm_settlement_data = {
                      "collected_by": "BPP",
                      "params": {
                        "bank_account_number": "xxxxxxxxxxxxxx",
                        "bank_code": "XXXXXXXX",
                      },
                      "status": "NOT-PAID",
                      "tags": [
                        {
                          "descriptor": {
                            "code": "BUYER_FINDER_FEES"
                          },
                          "display": False,
                          "list": [
                            {
                              "descriptor": {
                                "code": "BUYER_FINDER_FEES_PERCENTAGE"
                              },
                              "value": "0"
                            }
                          ]
                        },
                        {
                          "descriptor": {
                            "code": "SETTLEMENT_TERMS"
                          },
                          "display": False,
                          "list": [
                            {
                              "descriptor": {
                                "code": "SETTLEMENT_WINDOW"
                              },
                              "value": "PT60M"
                            },
                            {
                              "descriptor": {
                                "code": "SETTLEMENT_BASIS"
                              },
                              "value": "DELIVERY"
                            },
                            {
                              "descriptor": {
                                "code": "SETTLEMENT_TYPE"
                              },
                              "value": "UPI"
                            },
                            {
                              "descriptor": {
                                "code": "MANDATORY_ARBITRATION"
                              },
                              "value": "true"
                            },
                            {
                              "descriptor": {
                                "code": "COURT_JURISDICTION"
                              },
                              "value": "New Delhi"
                            },
                            {
                              "descriptor": {
                                "code": "DELAY_INTEREST"
                              },
                              "value": "0"
                            },
                            {
                              "descriptor": {
                                "code": "STATIC_TERMS"
                              },
                              "value": "https://example-test-bpp.com/static-terms.txt"
                            },
                            {
                              "descriptor": {
                                "code": "SETTLEMENT_AMOUNT"
                              },
                              "value": "0.0"
                            }
                          ]
                        }
                      ],
                      "type": "ON-FULFILLMENT"
                    }

location = {
            "country": {
                "code": "IND"
            },
            "city": {
                "code": "std:011"
            }
        }

search_payload_payments_obj = {
        "collected_by": "BPP",
        "tags": [
          {
            "descriptor": {
              "code": "BUYER_FINDER_FEES"
            },
            "display": False,
            "list": [
              {
                "descriptor": {
                  "code": "BUYER_FINDER_FEES_PERCENTAGE"
                },
                "value": "0"
              }
            ]
          },
          {
            "descriptor": {
              "code": "SETTLEMENT_TERMS"
            },
            "display": False,
            "list": [
              {
                "descriptor": {
                  "code": "DELAY_INTEREST"
                },
                "value": "0"
              },
              {
                "descriptor": {
                  "code": "STATIC_TERMS"
                },
                "value": "https://example-test-bap.com/static-terms.txt"
              }
            ]
          }
        ]
      }
